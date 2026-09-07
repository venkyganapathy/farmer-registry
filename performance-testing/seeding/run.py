#!/usr/bin/env python3
"""CLI entrypoint for the bulk seed generator. See README.md for the full
flow and design rationale. Usage:

    cd performance-testing/seeding
    python run.py --tier smoke
    python run.py --tier primary --dsn postgresql://...
"""

import argparse
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import db
from common import RANDOM_SEED
from generators import (
    crop, farm_inputs, farmer, history, household, household_member,
    land, livestock, membership_details,
)
from id_scheme import init_pod_id_scheme
from search_anchors import generate_anchors
from seed_manifest import ManifestBuilder

random.seed(RANDOM_SEED)

CHILD_GENERATORS = {
    "land": land.generate,
    "livestock": livestock.generate,
    "farm_inputs": farm_inputs.generate,
    "membership_details": membership_details.generate,
}


def per_parent_count(table_key: str) -> int:
    _, _, span = config.RATIOS[table_key]
    return random.randint(*span)


class TableSink:
    """One BatchWriter for the live table, one for its history twin, plus
    the tab/section lookup history rows need."""

    def __init__(self, conn, table_key: str, cursor_for_metadata):
        live_table, history_table, mnemonic = config.TABLE_NAMES[table_key]
        self.table_key = table_key
        self.mnemonic = mnemonic
        self.conn = conn
        self.live_table = live_table
        self.history_table = history_table
        self.live_writer = None
        self.history_writer = None
        self.tab_sections = history.load_tab_sections(cursor_for_metadata, mnemonic)
        self.live_count = 0
        self.history_count = 0

    def write_live(self, row: dict):
        if self.live_writer is None:
            self.live_writer = db.BatchWriter(self.conn, self.live_table, list(row.keys()))
        self.live_writer.add(row)
        self.live_count += 1

        # Every live insert gets a corresponding history insert (1:1, not a
        # sample) -- tab_id/section_id come from load_tab_sections(), i.e.
        # real g2p_register_sections/g2p_register_ui_tab_sections metadata,
        # not invented values.
        history_row = history.generate(row, self.tab_sections)
        if self.history_writer is None:
            self.history_writer = db.BatchWriter(self.conn, self.history_table, list(history_row.keys()))
        self.history_writer.add(history_row)
        self.history_count += 1

    def flush(self):
        if self.live_writer:
            self.live_writer.flush()
        if self.history_writer:
            self.history_writer.flush()


def run(tier: str, dsn_override: str | None, pod_index: int = 0, total_pods: int = 1):
    if dsn_override:
        config.DB_DSN = dsn_override

    total_target_farmers = config.DATA_VOLUME_TIERS[tier]
    
    # Calculate this pod's share of farmers
    farmers_per_pod = total_target_farmers // total_pods
    # Give the last pod any remainder
    if pod_index == total_pods - 1:
        target_farmers = total_target_farmers - (pod_index * farmers_per_pod)
    else:
        target_farmers = farmers_per_pod
    
    print(f"[seed] tier={tier} total_target={total_target_farmers} pod={pod_index}/{total_pods} target_farmers={target_farmers}")
    
    # Initialize pod-specific ID scheme to prevent duplicates
    init_pod_id_scheme(pod_index, total_pods, total_target_farmers)

    anchors = generate_anchors()
    manifest = ManifestBuilder(search_terms=anchors, data_volume=tier, pod_index=pod_index, total_pods=total_pods)

    conn = db.connect()
    metadata_cursor = conn.cursor()

    sinks = {key: TableSink(conn, key, metadata_cursor) for key in config.TABLE_NAMES}
    metadata_cursor.close()
    conn.commit()

    captured_indexes = {}
    if config.DEFER_INDEXES:
        print("[seed] deferring non-PK indexes for target tables")
        with conn.cursor() as cur:
            for key, (live_table, _, _) in config.TABLE_NAMES.items():
                captured_indexes[live_table] = db.capture_and_drop_indexes(cur, live_table)
        conn.commit()

    start = time.time()
    farmers_written = 0
    last_reported = 0
    report_every = 500_000

    while farmers_written < target_farmers:
        household_row = household.generate()
        sinks["household"].write_live(household_row)
        manifest.observe_household(household_row["internal_record_id"])

        for _ in range(per_parent_count("household_member")):
            member_row = household_member.generate(household_row)
            sinks["household_member"].write_live(member_row)

        for _ in range(per_parent_count("farmer")):
            if farmers_written >= target_farmers:
                break
            farmer_row = farmer.generate(household_row, anchors)
            sinks["farmer"].write_live(farmer_row)
            manifest.observe_farmer(farmer_row["internal_record_id"])
            farmers_written += 1

            for _ in range(per_parent_count("land")):
                land_row = land.generate(farmer_row)
                sinks["land"].write_live(land_row)
                for _ in range(per_parent_count("crop")):
                    crop_row = crop.generate(land_row)
                    sinks["crop"].write_live(crop_row)

            for table_key in ("livestock", "farm_inputs", "membership_details"):
                for _ in range(per_parent_count(table_key)):
                    row = CHILD_GENERATORS[table_key](farmer_row)
                    sinks[table_key].write_live(row)

        if farmers_written - last_reported >= report_every:
            last_reported = farmers_written
            elapsed = time.time() - start
            rate = farmers_written / elapsed if elapsed else 0
            print(f"[seed] farmers={farmers_written}/{target_farmers} ({rate:.0f}/s)")

    print("[seed] flushing remaining batches")
    for sink in sinks.values():
        sink.flush()
    conn.commit()

    if config.DEFER_INDEXES:
        print("[seed] rebuilding deferred indexes")
        with conn.cursor() as cur:
            for live_table, index_defs in captured_indexes.items():
                db.recreate_indexes(cur, index_defs)
        conn.commit()

    print("[seed] ANALYZE")
    with conn.cursor() as cur:
        for live_table, history_table, _ in config.TABLE_NAMES.values():
            db.analyze(cur, live_table)
            db.analyze(cur, history_table)
    conn.commit()

    manifest.write(config.SEED_MANIFEST_PATH)
    manifest_path = config.SEED_MANIFEST_PATH if total_pods == 1 else f"{config.SEED_MANIFEST_PATH.rsplit('.', 1)[0]}_pod{pod_index}.json"
    print(f"[seed] manifest written to {manifest_path}")

    for key, sink in sinks.items():
        print(f"[seed] {key}: live={sink.live_count} history={sink.history_count}")

    conn.close()
    print(f"[seed] done in {time.time() - start:.0f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tier", choices=list(config.DATA_VOLUME_TIERS), required=True)
    parser.add_argument("--dsn", default=None, help="overrides SEED_DB_DSN / config.DB_DSN")
    parser.add_argument("--pod-index", type=int, default=0, help="zero-based index of this pod (0 to total-pods-1)")
    parser.add_argument("--total-pods", type=int, default=1, help="total number of pods running in parallel")
    args = parser.parse_args()
    
    if args.pod_index >= args.total_pods:
        print(f"Error: pod-index ({args.pod_index}) must be less than total-pods ({args.total_pods})")
        sys.exit(1)
    
    run(args.tier, args.dsn, args.pod_index, args.total_pods)
