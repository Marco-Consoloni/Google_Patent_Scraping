import os
import json
import argparse
from scraping_functions import setup_driver, get_title, get_abstract, get_CPC_classes, get_first_claim, download_img


def scrape_documents_from_query(json_file_path, front_imgs_dir, json_dir): 
    """
    Scrapes patent documents based on citations from the specified JSON file.
    
    Parameters:
    - json_file_path (str): The path to the input JSON file containing patent data of a query patent.
    - front_imgs_dir (str): Directory where front images of patents will be saved.
    - json_dir (str): Directory where the scraped patent data will be saved as a JSON file.

    This function reads patent query data from a JSON file, extracts citation information.
    Then, for each cited patent, it scrapes the first claim and downloads the corresponding front image.
    """

    # Extract the patent ID of the corresponding query from the JSON file name (without extension)
    #query = os.path.splitext(os.path.basename(json_file_path))[0]

    # Determine the CPC class of the corresponding query from the directory structure of the JSON file path
    CPC_class = os.path.dirname(json_file_path).split(os.path.sep)[-1]

    # Create the output directory for JSON files based on the CPC class
    json_dir_CPC = os.path.join(json_dir, CPC_class)
    os.makedirs(json_dir_CPC, exist_ok=True)

    # Create the output directory for front images based on the CPC class
    front_imgs_dir_CPC = os.path.join(front_imgs_dir, CPC_class)
    os.makedirs(front_imgs_dir_CPC, exist_ok=True)

    # Initialize WebDriver
    driver = setup_driver()  
    
    # Open the json file for the patent query
    with open(json_file_path, 'r') as file:
        query_patent_ID = os.path.splitext(os.path.basename(json_file_path))[0]
        query_patent_data = json.load(file)
        citations_list = query_patent_data.get('citations_by_examiner') # Retrieve the list of patent IDs cited by the examiner.
        print(f'Starting scraping citations for query: {query_patent_ID}')

        # Initialize a counter to keep track of the number of document patents successfully retrieved
        retrieved_patents_count = 0 

        # Iterate over each patent ID in the citations list
        for patent_ID in citations_list:
            # Construct the Google Patents URL for the specific patent
            url = f"https://patents.google.com/patent/{patent_ID}/en?oq={patent_ID}" 

            try:
                # Scrape patent data 
                title = get_title(driver, url)
                abstract = get_abstract(driver, url)
                CPC_classes = get_CPC_classes(driver, url)
                fst_claim = get_first_claim(driver, url)
                front_img_path = download_img(driver, url, filename=patent_ID, save_dir=front_imgs_dir_CPC)

                # Ensure first claim, and front image are successfully retrieved
                if all([title, abstract, fst_claim, CPC_classes, front_img_path]):

                        # Create a dictionary to hold all the scraped data for this document patent  
                        document_patent_data = {
                            "type": "document",
                            "query": json_file_path,
                            "class": CPC_class,
                            "title": title,
                            "abstract": abstract,
                            "CPC_class": CPC_classes,
                            "first_claim": fst_claim,
                            "front_img": front_img_path 
                        }
                        
                        # Define the filename for the output JSON file based on the patent ID
                        json_filename = patent_ID + '.json'
                        json_filepath = os.path.join(json_dir_CPC, json_filename)

                        # Write the document patent data dictionary to a JSON file
                        with open(json_filepath, 'w') as json_file:
                            json.dump(document_patent_data, json_file, indent=2)
                            #print(f'{patent_ID} successfully scraped.')
                        
                        # Increment the count of successfully retrieved document patents
                        retrieved_patents_count += 1
            
            # Handle any exceptions that occur during scraping for a particular patent
            except Exception as e:
                print(f"Error processing patent {patent_ID} from {url}: {e}")
        
        # After processing all the cited patents, update the query patent data with the count of successfully retrieved document patents
        query_patent_data['document_patents_count'] = retrieved_patents_count

        # Write the updated query patent data back to the original JSON file
        with open(json_file_path, 'w') as file:
            json.dump(query_patent_data, file, indent=2)
            # Print a summary of the results, showing how many patents were successfully scraped fro a query patent
            print(f"document_patents_count is: {retrieved_patents_count}\t"
                f"{retrieved_patents_count}/{len(citations_list)}\t"
                f"{retrieved_patents_count * 100 / len(citations_list):.2f}%")

if __name__ == "__main__":

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Scrape Google Patents and save patent data for documents as JSON.')
    parser.add_argument('--json_dir_input', type=str, default='/vast/marco/Data_Google_Patent/json/query',
                        help='Directory to read JSON files.')
    parser.add_argument('--front_imgs_dir', type=str, default='/vast/marco/Data_Google_Patent/front_imgs/document',
                        help='Directory to save front images.')
    parser.add_argument('--json_dir_output', type=str, default='/vast/marco/Data_Google_Patent/json/document',
                        help='Directory to save JSON files.')
    #parser.add_argument('--CPC_to_exclude', type=list, default=[],
    #                    help='CPC file to exclude when resuming scraping.')

    args = parser.parse_args()  # Parse command-line arguments.

# Iterate through each CPC directory within the input JSON directory
for CPC_dir in os.listdir(args.json_dir_input):
    CPC_dir_path = os.path.join(args.json_dir_input, CPC_dir)
    print(f'Starting the scraping process for CPC: {CPC_dir} ------------------')

    # Iterate through each JSON file in the current CPC directory.
    for json_file in os.listdir(CPC_dir_path):
        json_file_path = os.path.join(CPC_dir_path, json_file)
        scrape_documents_from_query(json_file_path, args.front_imgs_dir, args.json_dir_output)
    
    print(f'Completed scraping process for CPC: {CPC_dir} ----------------------')

            
