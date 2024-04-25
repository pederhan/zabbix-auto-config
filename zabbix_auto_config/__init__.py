from __future__ import annotations

import datetime
import json
import logging
import multiprocessing
import os
import os.path
import time
from pathlib import Path
from typing import List

import multiprocessing_logging  # type: ignore[import]
import tomli

from zabbix_auto_config.hostmodifiers.load import load_host_modifiers
from zabbix_auto_config.sourcecollectors.load import load_source_collectors

from . import models
from . import processing
from .__about__ import __version__
from ._types import HealthDict
from ._types import SourceHostsQueue
from .state import get_manager


def get_config() -> models.Settings:
    cwd = os.getcwd()
    config_file = os.path.join(cwd, "config.toml")
    with open(config_file) as f:
        content = f.read()
    config_dict = tomli.loads(content)
    config = models.Settings(**config_dict)
    return config


def write_health(
    health_file: Path,
    processes: List[processing.BaseProcess],
    queues: List[SourceHostsQueue],
    failsafe: int,
) -> None:
    now = datetime.datetime.now()
    health: HealthDict = {
        "date": now.isoformat(timespec="seconds"),
        "date_unixtime": int(now.timestamp()),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "all_ok": all(p.state.ok for p in processes),
        "processes": [],
        "queues": [],
        "failsafe": failsafe,
    }

    for process in processes:
        health["processes"].append(
            {
                "name": process.name,
                "pid": process.pid,
                "alive": process.is_alive(),
                **process.state.asdict(),
            }
        )

    for queue in queues:
        health["queues"].append(
            {
                "size": queue.qsize(),
            }
        )

    try:
        with open(health_file, "w") as f:
            f.write(json.dumps(health))
    except Exception as e:
        logging.error("Unable to write health file %s: %s", health_file, e)


def log_process_status(processes: List[processing.BaseProcess]) -> None:
    process_statuses: List[str] = []

    for process in processes:
        process_name = process.name
        process_status = "alive" if process.is_alive() else "dead"
        process_statuses.append(f"{process_name} is {process_status}")

    logging.info("Process status: %s", ", ".join(process_statuses))


def main() -> None:
    multiprocessing_logging.install_mp_handler()
    logging.basicConfig(
        format="%(asctime)s %(levelname)s [%(processName)s %(process)d] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        level=logging.DEBUG,
    )
    config = get_config()
    logging.getLogger().setLevel(config.zac.log_level)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    logging.info("Main start (%d) version %s", os.getpid(), __version__)
    stop_event = multiprocessing.Event()
    state_manager = get_manager()

    # Import host modifier and source collector modules
    host_modifiers = load_host_modifiers(config)
    source_collectors = load_source_collectors(config)

    # Initialize source collector processes from imported modules
    source_hosts_queues: List[SourceHostsQueue] = []
    src_processes: List[processing.BaseProcess] = []
    for source_collector in source_collectors:
        # Each source collector has its own queue
        source_hosts_queue: SourceHostsQueue = multiprocessing.Queue(maxsize=1)
        source_hosts_queues.append(source_hosts_queue)
        process: processing.BaseProcess = processing.SourceCollectorProcess(
            source_collector.name,
            state_manager.State(),
            source_collector,
            source_hosts_queue,
        )
        src_processes.append(process)

    # Initialize the other processes
    processes: List[processing.BaseProcess] = [
        processing.SourceHandlerProcess(
            "source-handler",
            state_manager.State(),
            config.zac.db_uri,
            source_hosts_queues,
        ),
        processing.SourceMergerProcess(
            "source-merger",
            state_manager.State(),
            config.zac.db_uri,
            host_modifiers,
        ),
        processing.ZabbixHostUpdater(
            "zabbix-host-updater",
            state_manager.State(),
            config.zac.db_uri,
            config,
        ),
        processing.ZabbixHostgroupUpdater(
            "zabbix-hostgroup-updater",
            state_manager.State(),
            config.zac.db_uri,
            config,
        ),
        processing.ZabbixTemplateUpdater(
            "zabbix-template-updater",
            state_manager.State(),
            config.zac.db_uri,
            config,
        ),
    ]

    # Combine the source collector processes with the other processes
    processes.extend(src_processes)

    # Abort if we can't start _all_ processes
    for pr in processes:
        try:
            pr.start()
        except Exception as e:
            logging.error("Unable to start process %s: %s", pr.name, e)
            stop_event.set()  # Stop other proceses immediately
            break

    with processing.SignalHandler(stop_event):
        status_interval = 60
        next_status = datetime.datetime.now()

        while not stop_event.is_set():
            if next_status < datetime.datetime.now():
                if config.zac.health_file is not None:
                    write_health(
                        config.zac.health_file,
                        processes,
                        source_hosts_queues,
                        config.zabbix.failsafe,
                    )
                log_process_status(processes)
                next_status = datetime.datetime.now() + datetime.timedelta(
                    seconds=status_interval
                )

            dead_process_names = [
                process.name for process in processes if not process.is_alive()
            ]
            if dead_process_names:
                logging.error(
                    "A child has died: %s. Exiting", ", ".join(dead_process_names)
                )
                stop_event.set()

            time.sleep(1)

        logging.debug(
            "Queues: %s",
            ", ".join([str(queue.qsize()) for queue in source_hosts_queues]),
        )

        for pr in processes:
            logging.info("Terminating: %s(%d)", pr.name, pr.pid)
            pr.terminate()

        def get_alive():
            return [process for process in processes if process.is_alive()]

        while alive := get_alive():
            log_process_status(processes)
            for process in alive:
                logging.info("Waiting for: %s(%d)", process.name, process.pid)
                process.join(10)
                if process.exitcode is None:
                    logging.warning(
                        "Process hanging. Signaling new terminate: %s(%d)",
                        process.name,
                        process.pid,
                    )
                    process.terminate()
            time.sleep(1)

    logging.info("Main exit")


if __name__ == "__main__":
    main()
