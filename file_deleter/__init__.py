__author__ = 'TetraEtc'

from slacker import Slacker
import sys
from datetime import timedelta, datetime


def main(token, weeks=4):
    slack = Slacker(token)
    # Get list of all files available for the user of the token
    total = slack.files.list(count=1).body['paging']['total']
    num_pages = int(total/1000.00 + 1)
    print("{} files to be processed, across {} pages".format(total, num_pages))
    # Get Data about files
    files_to_delete = []
    ids = [] # For checking that the API doesn't return duplicate files
    count = 1
    for page in range(num_pages):
        print ("Pulling page number {}".format(page + 1))
        files = slack.files.list(count=1000, page=page+1).body['files']
        for file in files:
            print("Checking file number {}".format(count))
            # Checking for duplicates
            if file['id'] not in ids:
                ids.append(file['id'])
                if datetime.fromtimestamp(file['timestamp']) < datetime.now() - timedelta(weeks=weeks):
                    files_to_delete.append(file)
                    print("File No. {} will be deleted".format(count))
                else:
                    print ("File No. {} will not be deleted".format(count))
            count+=1

    print("All files checked\nProceeding to delete files")
    print("{} files will be deleted!".format(len(files_to_delete)))
    count = 1
    for file in files_to_delete:
        print("Deleting file {} of {}".format(count, len(files_to_delete)))
        slack.files.delete(file_=file['id'])
        print("Deleted Successfully")
        count+=1

    return count-1




if __name__ == "__main__":
    try:
        token = sys.argv[1:]
    except IndexError:
        print("Usage: python file_deleter.py api_token\nPlease provide a value for the API Token")
        sys.exit(2)

    main(token[0])
