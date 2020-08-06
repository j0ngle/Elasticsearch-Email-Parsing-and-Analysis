# Elasticsearch-Email-Parsing-and-Analysis
Personal project to practice Elasticsearch and Kibana by parsing and analyzing emails

Functions as follows: 
    Takes in and unzips .zip file
    Determines the extracts files and determines file types (Cannot handle folders yet)
        For .MBOX:
            Iterates through every email in the .mbox file and stores the plain text, then indexes it in ES
            If an email has attachments, it sends them to the main file handling method
        For .PDF:
            Opens the PDF and creates a new dictionary with its metadata
            Sends a JSON to the parser
        For .TXT:
            Sends the text to the parser
    Parses the file accordingly and creates an index for each file and email in ES
    
    Once all the indexes are completed, Kibana displays the analytics on a dashboard
    
    NOTE: I am well away the parsing algorithm is garbage, it's just a placeholder. I'll fix it someday in the future
