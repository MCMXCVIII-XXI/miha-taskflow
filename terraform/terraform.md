
# Miha-TaskFlow Terraform Infrastructure

This repository contains a modular Terraform setup for Yandex Cloud. It is designed to keep environment-specific values separate from reusable infrastructure code, so the same project can safely manage both development and production environments without duplicating logic.

## What this project does

This Terraform layout provisions a small but scalable cloud foundation:

- A private VPC network.
    
- A subnet for internal resources.
    
- A security group with controlled SSH and application access.
    
- A base VM module that is reused by multiple service roles.
    
- Public and private IP outputs for follow-up automation such as Ansible.
    

The current architecture is built around these roles:

- `app`
    
- `db`
    
- `redis`
    
- `workers`
    
- `monitoring`
    
- `search`
    
- `edge`
    

`app` and `edge` are the externally reachable machines, while the others stay private and communicate over the internal network.

## Repository structure

text

`. ├── envs │   ├── dev │   │   ├── main.tf │   │   ├── outputs.tf │   │   ├── terraform.tfvars │   │   └── variables.tf │   └── prod │       ├── main.tf │       ├── outputs.tf │       ├── terraform.tfvars │       └── variables.tf └── modules     ├── app    ├── db    ├── edge    ├── monitoring    ├── network    ├── redis    ├── search    ├── security_group    ├── vm    └── workers`

`envs/dev` and `envs/prod` are root modules. They assemble the infrastructure for each environment. `modules/*` are reusable building blocks that contain the actual implementation logic.

## How the modules are organized

## `modules/network`

Creates the VPC and subnet. It exists only to keep network logic isolated and reusable.

## `modules/security_group`

Creates cloud firewall rules. SSH is restricted to allowed CIDRs, and application ports can be opened explicitly.

## `modules/vm`

Creates a single VM. It receives all machine parameters, image, disk, security group, SSH key, and cloud-init data, then outputs instance and IP information.

## Role modules

`app`, `db`, `redis`, `workers`, `monitoring`, `search`, and `edge` are thin wrappers around `modules/vm`. They do not introduce new infrastructure logic; they only define the role-specific machine parameters.

## Security model

SSH is not open to everyone. Access is limited to the IP ranges listed in `allowed_ssh_cidrs`.

Only machines that need to be reachable from outside should have public IPs. In this project that is usually `app` and `edge`. Internal services stay private.

Outbound traffic is allowed at the beginning so the machines can update packages, pull containers, and reach external services. You can tighten outbound rules later if needed.

## Prerequisites

Before running this project, make sure you have:

- Terraform installed.
    
- Yandex Cloud CLI (`yc`) installed and configured.
    
- Access to a Yandex Cloud cloud and folder.
    
- A valid SSH public key.
    
- A trusted IP or VPN range for SSH access.
    

## Authentication

Terraform must authenticate to Yandex Cloud before it can create resources. The recommended workflow is to obtain the required values first, then pass them into Terraform.

For local use, the simplest approach is to export variables in your shell:

bash

`export TF_VAR_yc_token="$(yc iam create-token)" export TF_VAR_cloud_id="$(yc config get cloud-id)" export TF_VAR_folder_id="$(yc config get folder-id)"`

If you use a service account key file instead, pass it through the provider configuration or a dedicated variable.

## Configuration

Each environment has its own `terraform.tfvars` file.

That file should contain values such as:

- project name,
    
- environment name,
    
- zone,
    
- CIDR block,
    
- cloud and folder IDs,
    
- Terraform authentication values,
    
- SSH public key,
    
- allowed SSH CIDRs,
    
- security group rules,
    
- resource sizes for each role.
    

Before deploying, replace any placeholders such as:

- `YOUR_IP/32`
    
- `ssh-ed25519 AAAA...`
    
- placeholder cloud-init values
    

## Quick start

## 1. Select the environment

bash

`cd envs/dev`

Use `envs/prod` if you want to deploy production infrastructure.

## 2. Initialize Terraform

bash

`terraform init`

This downloads the provider and prepares all modules.

## 3. Format the code

bash

`terraform fmt`

This keeps the configuration clean and consistent.

## 4. Validate the config

bash

`terraform validate`

This checks the configuration for syntax and internal consistency.

## 5. Review the plan

bash

`terraform plan`

The plan shows exactly what Terraform will create. Review networking rules, machine sizes, and public IP assignments carefully.

## 6. Apply the configuration

bash

`terraform apply`

Terraform will ask for confirmation before creating anything.

## Outputs

After the apply finishes, use the outputs for automation and connection setup:

- `app_public_ip`
    
- `app_private_ip`
    
- `db_private_ip`
    
- `redis_private_ip`
    
- `workers_private_ip`
    
- `monitoring_private_ip`
    
- `search_private_ip`
    
- `edge_public_ip`
    
- `edge_private_ip`
    

## Learning path behind this layout

This project follows a practical progression:

1. Learn `yc` CLI and authentication.
    
2. Create a minimal Terraform setup.
    
3. Build a simple VPC module.
    
4. Expand it into a modular multi-environment architecture.
    
5. Reuse the same VM building block for all service roles.
    

That progression makes the project easier to understand and much easier to maintain than a single large Terraform file.

## Notes for contributors

- Do not hardcode secrets in Terraform.
    
- Do not expose SSH to `0.0.0.0/0` unless there is a strong reason.
    
- Keep networking resources in the root environment modules.
    
- Keep `modules/vm` as the single source of truth for VM creation.
    
- Keep `dev` and `prod` structurally aligned whenever possible.
    

## Future work

The structure is intentionally simple and can grow later without becoming messy. Additional services or more advanced networking can be added by following the same pattern: small root modules for environments and reusable child modules for infrastructure building blocks.



