from argparse import ArgumentParser
from src.db.database import Database
from src.api.lightning_client import get_channel_lists, get_channel_data

def main():
    parser = ArgumentParser(description="Lightning Node Database CLI")
    parser.add_argument('--delete', type=int, help='Delete data older than x months')

    args = parser.parse_args()

    db = Database()

    if args.delete:
        db.delete_old_data(args.delete)

    channel_lists = get_channel_lists()
    db.update_channel_lists(channel_lists)

    for channel in channel_lists:
        channel_data = get_channel_data(channel['channel_id'])
        db.update_channel_data(channel['id'], channel_data)

if __name__ == "__main__":
    main()