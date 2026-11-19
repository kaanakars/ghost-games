# Deploying the web app to Azure

The app runs on **Azure Container Apps**. After the one-time setup below,
every push to `main` that passes the tests is deployed automatically.

```
push to main ──► test (ruff + pytest, incl. every app page)
             ──► build Docker image (linux/amd64) ──► GitHub Container Registry
             ──► deploy that image to Azure Container Apps
```

## Why Container Apps, not App Service
The first plan was App Service (Web App for Containers). On an Azure for
Students subscription, App Service quota started at **0 servers**, for both
the paid Basic tier and the free tier, so no plan could be created.

Container Apps uses a different quota and fits this app better anyway:
- **Scales to zero** when nobody is visiting, so it costs nothing while idle.
  The monthly free allowance covers a portfolio app.
- Runs the same Docker image, so nothing else in the project changed.
- Trade-off: the first visit after a quiet spell waits about 30 seconds while
  the app starts.

## 0. Tools (Mac)
```bash
brew install azure-cli
az login
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
```
The `provider register` lines switch Container Apps and its logging on for
the subscription, once.

## 1. First push builds the image
Push to `main`. The `deploy` job is skipped until step 3, but `test` and
`build` run and the image appears under **Packages** on GitHub.

Make the package public so Azure can pull it without a password:
GitHub → your profile → **Packages** → `ghost-games` → **Package settings** →
**Change visibility** → Public.

## 2. Create the Azure resources
```bash
az group create --name ghost-games-rg --location canadacentral

# the environment: the network and logging space the app lives in
az containerapp env create --name ghost-games-env \
  --resource-group ghost-games-rg --location canadacentral

az containerapp create --name ghost-games --resource-group ghost-games-rg \
  --environment ghost-games-env --image ghcr.io/kaanakars/ghost-games:latest \
  --target-port 8000 --ingress external \
  --min-replicas 0 --max-replicas 1 --cpu 0.5 --memory 1.0Gi \
  --query properties.configuration.ingress.fqdn -o tsv
```
The last command prints the app's address; open it with `https://`.

| Setting | Why |
|---|---|
| `--target-port 8000` | Streamlit listens on 8000 inside the container |
| `--ingress external` | Reachable from the internet |
| `--min-replicas 0` | Scale to zero when idle, so idle time is free |
| `--max-replicas 1` | One copy only: Streamlit keeps each visitor's session in memory |
| `--cpu 0.5 --memory 1.0Gi` | Plenty for a read-only app |

## 3. Let GitHub Actions deploy
GitHub signs in with a **service principal**: a robot account that may only
change this one resource group.
```bash
SUB=$(az account show --query id -o tsv)
az ad sp create-for-rbac --name ghost-games-deploy --role contributor \
  --scopes /subscriptions/$SUB/resourceGroups/ghost-games-rg --json-auth \
  | gh secret set AZURE_CREDENTIALS
gh variable set AZURE_CONTAINERAPP_NAME --body ghost-games
gh variable set AZURE_RESOURCE_GROUP --body ghost-games-rg
```
The credentials go straight from Azure into a GitHub secret: they never show
on screen or end up in a file.

Re-run the workflow (Actions → CI/CD → Run workflow). All three jobs should
be green, and the app should show a new revision:
```bash
az containerapp revision list --name ghost-games --resource-group ghost-games-rg -o table
```

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Current Limit (B1 VMs): 0` | App Service quota is 0 on this subscription: use Container Apps (this guide) |
| First page load is slow | Normal after idle time: the app scales up from zero |
| Image pull failed | The GitHub package is still private (step 1) |
| `Insufficient privileges` on `create-for-rbac` | The account can't create service principals; deploy by hand with the `az containerapp update` line from the workflow |
| Something else | `az containerapp logs show --name ghost-games --resource-group ghost-games-rg --follow` |

## Local run
```bash
pip install -r app/requirements.txt
streamlit run app/Home.py

# or the same container Azure runs:
docker buildx build --platform linux/amd64 -t ghost-games .
docker run -p 8000:8000 ghost-games      # http://localhost:8000
```

## Updating the numbers
The app reads only `app/data/`. After changing the analysis, re-export and push:
```bash
ghost-games-export
```
