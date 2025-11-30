# Fast IP Rotation (Hot Swap)

The goal is to drastically reduce the time to change IPs by modifying the network interface of a running VM, rather than destroying and recreating the entire VM.

## User Review Required
> [!IMPORTANT]
> **Architecture Change**: Child VMs will now be **persistent** (long-running). They will run a loop internally: `Run Crawler` -> `Swap IP` -> `Repeat`.
> **Cost Implication**: You will pay for the VM uptime continuously, but you save on boot time overhead.
> **Prerequisite**: The Child VMs need permission to modify their own network settings.

## Proposed Changes

### crawler-go/gcp
#### [NEW] [child_runner.sh](file:///c:/Users/solidityDeveloper/crawler_web_opener/crawler-go/gcp/child_runner.sh)
- A script that runs inside the Child VM.
- **Loop**:
    1.  **Run Crawler**: Execute the Docker container.
    2.  **Rotate IP**:
        -   Get current Instance Name, Zone, Project via Metadata.
        -   Call GCP API `deleteAccessConfig` (Detach IP).
        -   Call GCP API `addAccessConfig` (Attach new random IP).
    3.  **Sleep**: Optional short delay.

#### [MODIFY] [deploy.sh](file:///c:/Users/solidityDeveloper/crawler_web_opener/crawler-go/gcp/deploy.sh)
- **Remove** the self-destruct logic.
- **Update Startup Script**: Instead of running docker once, download and run `child_runner.sh`.
- **Instance Management**: Only create instances if they don't exist (scale up/down logic).

### crawler-go/terraform
#### [MODIFY] [compute.tf](file:///c:/Users/solidityDeveloper/crawler_web_opener/crawler-go/terraform/compute.tf)
- Ensure the Service Account used by Child VMs has `compute.instances.update` permission. (Currently using default SA, might need a custom one or IAM binding).

## Verification Plan
1.  **Deploy**: Update Mother VM with new scripts.
2.  **Monitor**: Watch `crawler_loop.log`.
3.  **Verify IP**: Check the external IP of a child VM in GCP Console, wait for "Rotate" log, check IP again. It should change without the VM restarting.
