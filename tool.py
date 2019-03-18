import argparse
import sys

from gdrive import upload, download

EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def main(action: str, src_file: str, dst_file: str):
    try:
        if action == 'put':
            upload(src_file, dst_file)
        elif action == 'get':
            download(src_file, dst_file)
        else:
            print("Argparse not configured properly", file=sys.stderr)
    except Exception as e:
        print(e)
        exit(EXIT_FAILURE)
    exit(EXIT_SUCCESS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='App for upload/downlide files to google drive. '
                    'It requires credetials.json file with google drive '
                    'client_id and client_secret.')

    parser.add_argument('act', choices=['get', 'put'],
                        help="Chose 'get' or 'post' action for downloading "
                             "or uploading files ")

    parser.add_argument('--src', action='store', dest='src', required=True,
                        type=str, help='Source file path')
    parser.add_argument('--dst', action='store', dest='dst', required=True,
                        type=str, help='Destination file path')
    args = parser.parse_args()

    main(args.act, args.src, args.dst)
