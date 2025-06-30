import argparse
from pathlib import Path
from poll_config import ConfigData, read_config
from vote_reader import parse_vote_file


def main() -> None:
    parser = argparse.ArgumentParser(
        "Teller", description="A preferential vote counter program."
    )
    parser.add_argument(
        "config_file", type=Path, help="Path to the configuration json file."
    )
    parser.add_argument("vote_file", type=Path, help="Path to the vote csv file.")

    parser.add_argument(
        "--ignore-invalid-votes",
        action="store_true",
        help="If invalid votes should raise an error, or if they should be simply discarded.",
    )

    args = parser.parse_args()

    # Sanity Checking
    config_file: Path = args.config_file
    vote_file: Path = args.vote_file
    assert (
        config_file.is_file()
    ), f"No file found at config file location: {config_file}"
    assert vote_file.is_file(), f"No file found at vote file location: {vote_file}"

    with open(config_file) as fp:
        config = read_config(fp)

    with open(vote_file) as fp:
        votes = parse_vote_file(fp)

    print(config)
    print(votes)


if __name__ == "__main__":
    main()
