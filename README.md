# Google Analytics 4 Plugin

This Dataiku DSS plugin provides a read connector to retrieve reports from [Google Analytics](https://analytics.google.com/).

Documentation: https://www.dataiku.com/product/plugins/google-analytics-4/

## How to install

There are two authentication modes that can be used for the plugin to access a Google Analytics account: via sharing with a service account, or direct access using Google’s Single Sign On.
From the [Google service account tab](https://console.developers.google.com/iam-admin/serviceaccounts), create a new Google Cloud Platform project:
- Select a project > New Project and fill in the required information.
- Enable the [Google Analytics API](https://console.cloud.google.com/apis/api/analytics.googleapis.com) for your project

### Using a service account

You have to create a service account for you GCP project:
- In the service accounts tab, click on create service account
- Fill in the details and skip step 2 if you want
- On step 3, create a key using the JSON format
- Save the key and open it with a text editor. You can press Done
- Write down the service account’s email address for later use
- Go to the plugin’s settings page to add a preset (Applications > Plugins > Google Analytics > Settings > Service Accounts > +Add preset)
- In the `Access credentials` box, paste the JSON key copied from your text editor
- Share the preset with the relevant Dataiku groups

### Setting up Single Sign On authentication

#### As a Dataiku administrator

- In the [credential tabs](https://console.cloud.google.com/apis/credentials) of your Google Cloud Platform project, create a new credential OAuth Client ID with a **Desktop app** application type
- In the **Authorized redirect URIs** section, add the domain of your Dataiku instance redirection endpoint. The structure should be `https://<<your instance domain>><<:port number if not 443>>/dip/api/oauth2-callback`
- Copy the client ID / client secret codes
- Create an OAuth consent screen, if not already done for your GCP project. You will need to save the form, but the screen does not need to be verified at this stage.
- On Dataiku, go to the plugin’s settings page to add a preset (Applications > Plugins > Google Analytics > Settings > Google Single Sign On > +Add preset)
- Paste client ID / client secret generated at the second step
- Make the preset useable by everybody

#### As a Dataiku user

Each Dataiku user has to allow google to share their data with DSS. To do so, go to your profile page > Credentials > << name of the preset created by the DSS administrator >> > 📝. This will trigger the SSO session where the user can log on their Google Analytics account and authorize Dataiku to access the data.

## How to use

- In your project flow, create a new dataset by selecting Dataset > Google Analytics > Get Reports (GA4)
- Select the appropriate authentication mode (Service account or individual account)
- Fill in the requested parameters in the connector's interface and
- Press **Test & Get Schema** when ready.

### Licence

Copyright 2023 Dataiku SAS

This plugin is distributed under the Apache License version 2.0
