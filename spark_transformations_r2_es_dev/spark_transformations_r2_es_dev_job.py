
import argparse
import zipfile
import os

# unzip the utils file  
try:
    with zipfile.ZipFile('{}/utils.zip'.format(os.getcwd()),"r") as zip_ref: zip_ref.extractall()
except Exception as e:
    try:
        with zipfile.ZipFile('/utils.zip'.format(os.getcwd()),"r") as zip_ref: zip_ref.extractall()
    except Exception as e:
        print(e)

        print("Path at terminal when executing this file")
        print(os.getcwd() + "\n")

        print("This file path, relative to os.getcwd()")
        print(__file__ + "\n")

        print("This file full path (following symlinks)")
        full_path = os.path.realpath(__file__)
        print(full_path + "\n")

        print("This file directory and name")
        path, filename = os.path.split(full_path)
        print(path + ' --> ' + filename + "\n")

        print("This file directory only")
        print(os.path.dirname(full_path))

        direct = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(path) for f in filenames] 
        print("all directoriesy and files")
        print(direct)

# TODO ADD your IMPORT FROM UTILS
# from utils.xxx import zzz as yy


            
def run():
    
    # Reading Args (production)
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", help="start_date")
    parser.add_argument("--end", help="end_date")
    args = parser.parse_args()
    start_date = args.start
    end_date =args.end

    print("[Starting] Job set up using start date {} and end date {}".format(start_date,end_date))

    # unit_testing = False

    # TODO ADD THE REST OF YOUR CODE

    
if __name__ == "__main__":
    run()
