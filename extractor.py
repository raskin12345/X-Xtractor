import re

# Sample collected tweets
with open ('collected_tweets.txt','r', encoding='utf-8') as collected_tweets_file:
    collected_tweets = collected_tweets_file.read()

# Refined regex for IPs (handles obfuscation [.] and full capture)
ip_regex = r"((?:\d{1,3}(?:\[\.\]|\.)?){3}\d{1,3})"

# Updated regex for full domains, handles subdomains, and multiple-level domains, including obfuscation [.]
domain_regex =  r"\b(?:[a-zA-Z0-9-]+\[?\.\]?)+[a-zA-Z]{2,}\b"

# Regex for hash extraction (SHA256)
hash_regex = r"\b([a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b"

def extract_iocs(text):
    # Extract IPs
    ips = re.findall(ip_regex, text)
    
    # Extract domains
    domains = re.findall(domain_regex, text)
    
    # Extract hashes
    hashes = re.findall(hash_regex, text)
    
    return ips, domains, hashes

# Example processing the tweets and extracting the IOCs
ips, domains, hashes = extract_iocs(collected_tweets)

# Remove obfuscation by replacing '[.]' with '.'
ips = [ip.replace("[.]", ".") for ip in ips]
domains = [domain.replace("[.]", ".") for domain in domains]

# Printing the extracted IOCs
clean_ip_regex = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
clean_ip_extracted = [ip for ip in ips if re.match(clean_ip_regex, ip)]
print("Extracted IPs:", set(clean_ip_extracted))
print("Extracted Domains:", set(domains))
print("Extracted Hashes:", set(hashes))
print(len(clean_ip_extracted)+len(domains)+len(hashes))
for i in set(clean_ip_extracted):
    print(i)
for i in set(hashes):
    print(i)