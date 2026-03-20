# GitHub Secrets Setup

## Required Secrets

To deploy this bot, set up the following secrets in your GitHub repository:

### Settings → Secrets and variables → Actions

| Secret Name | Description | Example |
|------------|-------------|---------|
| `CHANNEL_ID` | Telegram channel ID for greetings | `-1001740302927` |
| `DOCKERHUB_TOKEN` | Docker Hub access token (optional) | `xxxx` |

## How to Get Channel ID

1. Add @userinfobot to your channel
2. Forward any message from the channel to the bot
3. The bot will reply with the channel ID

Or ask channel admin to get the ID via @getidsbot

## Setup Instructions

1. Go to repository Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `CHANNEL_ID` with your channel's Telegram ID
4. Secrets are automatically available in workflows as `${{ secrets.CHANNEL_ID }}`
