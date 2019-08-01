"""Data downloader module"""
from __future__ import print_function
# import sys
# import click
import math
import requests
from tqdm import tqdm


def download_from_url(url, filename):
    # Streaming, so we can iterate over the response.
    r = requests.get(url, stream=True)

    # raise an exception in case of issue
    r.raise_for_status()

    # Total size in bytes.
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0
    with open(filename, 'wb') as f:
        for data in tqdm(r.iter_content(block_size),
                         total=math.ceil(total_size // block_size),
                         unit='KB', unit_scale=True):
            wrote = wrote + len(data)
            f.write(data)
    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong")

    print('\n')


def download_from_ddl_def(ddl_file, csv_path):
    """"""
    with open(ddl_file) as f:
        ddl_url = f.readline().strip('\n\r')

    print("== Downloading file from {url} to {dst}".format(url=ddl_url, dst=csv_path))
    download_from_url(ddl_url, csv_path)


# @click.command('ddl_data')
# @click.option('--ddl_file', help='File containing information on the file to download. Extension should be .ddl')
# @click.option('--dst_path', help='Destination path where the file should be downloaded')
# def main(ddl_file, dst_path):
#     """Click command corresponding to download_from_ddl_def"""
#     download_from_ddl_def(ddl_file, dst_path)
#
#
# if __name__ == "__main__":
#     sys.exit(main())
