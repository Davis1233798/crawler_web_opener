- **Validation**: Filters proxies by testing connection to `httpbin.org`. *Note: Free proxies often have low availability.*
- **Browser Automation**: Launches headless (or headful) browsers and simulates activity.

## Troubleshooting

- **No working proxies**: The script will retry every 60 seconds. Free proxies are unreliable; consider using a paid proxy service or a better list for production use.
- **Browser errors**: Ensure Playwright is installed correctly.
