# auth0-lambda-configurator description
Lambda function for dynamic configuration of AUTH0 applications. Sets the:

* callbacks,
* web_origins,
* allowed_origins,
* allowed_logout_urls.

For more see this blog post: https://medium.com/@kszarlej94/dynamic-environments-with-auth0-ed48579be3

## configuration
Lambda is configured through *config.py* file and SSM. Lambda expects to get from SSM two parameters - auth0 *client_id* and client_secret for machine-to-machine application on behalf which lambda makes API calls. Path where lambda looks for these parameters can be configured through *config.py* file.

Also a parameter AUTH0_API_URL should be set in *config.py*. It is your account's Auth0 API path eg. *kszarlej.eu.auth0.com*

For howto on setting auth0 application see this blog post: https://medium.com/@kszarlej94/dynamic-environments-with-auth0-ed48579be3

## deployment 
An example *serverless.yml* file is included. Make sure to modify the YOUR_ACCOUNT_ID and YOUR_DEPLOYMENT_BUCKET inside. 

To deploy use serverless:

```bash
$ serverless deploy
```

## configure function
Function should be invoked with the following payload:

```json
{
  "client_id": "AUTH0_CLIENT_ID_YOU_CAN_OBTAIN_IT_FROM_AUTH0_DASHBOARD",
  "callback_path": "PATH_WHERE_AUTH0_SENDS_CALLBACK",
  "domain": "DOMAIN_WHICH_HAS_TO_BE_WHITELISTED"
}
```

Make sure to prepend proper scheme (http or https depending on your website) to domain.

Domain from payload will be put in `allowed_origins`, `web_origins`, `allowed_logout_urls` settings. For `callbacks` field concatenation of `domain` + / + `callback_path` will be used.

### Example invocation

```bash
$ aws lambda invoke --function-name serverless-auth0-lambda-staging-configure --payload '{"client_id": "sTeJ6uofVE3vTew6jHNHGUzLpg9sZgMT", "callback_path": "/callback", "domain":"https://example.com"}' /dev/null
```
