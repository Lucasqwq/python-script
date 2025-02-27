def generate_nginx_config(input_file):
    # Template for the Nginx configuration
    config_template = """server {{
    include tmp/api;
    listen 443 ssl;
    server_name api.{};
    ssl_certificate         /home/ubuntu/ssl/{}/fullchain.pem;
    ssl_certificate_key     /home/ubuntu/ssl/{}/privkey.pem;

    include /etc/nginx/sites-enabled/http_block_header.conf;
    include /etc/nginx/sites-enabled/http_block_ip.conf;

    access_log /data/logs/nginx/api/api.{}_access.log access;
    error_log  /data/logs/nginx/api/api.{}_error.log;

}}"""

    try:
        # Read domain names from input file
        with open(input_file, 'r') as f:
            domain_names = [line.strip() for line in f if line.strip()]

        # Generate a separate config file for each domain
        for domain in domain_names:
            # Generate the output filename with domain name using explicit string concatenation
            output_file = "api." + domain + ".conf"

            # Format the config content for this domain with 5 arguments
            config_content = config_template.format(
                domain,    # for server_name
                domain,    # for ssl_certificate
                domain,    # for ssl_certificate_key
                domain,    # for access_log
                domain     # for error_log
            )

            # Write to output file
            with open(output_file, 'w') as f:
                f.write(config_content)

            print(f"Generated configuration file: {output_file}")

        print(f"\nProcessed {len(domain_names)} domains successfully.")

    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Specify your input file containing domain names (one per line)
    input_file = "domains.txt"
    generate_nginx_config(input_file)
