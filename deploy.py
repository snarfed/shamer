#!/usr/bin/env python

import subprocess, os, sys, uuid, re
DEVNULL = open(os.devnull, 'w')

def call_without_output(cmd):
	return subprocess.call(cmd, stdout=DEVNULL, stderr=DEVNULL)

def prompt(instructions):
	return raw_input(instructions + ": ")

def clear():
	subprocess.call('cls' if os.name == 'nt' else 'clear')

def check_for_heroku():
	if call_without_output(['which', 'heroku']) == 1:
		sys.exit('Please install and set up the heroku toolbelt before running this script!')
	print 'Checking your heroku credentials...'
	subprocess.call(['heroku', 'auth:whoami'])
	print
	print 'Welcome to the github-s3-auth deployer script!'
	print 'Please enter the following config vars.'
	print

def prompt_with_condition(message, condition, error):
	done = False
	while not done:
		inp = prompt(message)
		if not condition(inp):
			print error
		else:
			done = True
	return inp

def prompt_need_response(var):
	return prompt_with_condition(var, lambda x: len(x) > 0, 'you must enter a {}'.format(var))

def get_params():
	APP_NAME = prompt('heroku app name (blank for random)') or ''
	SK = prompt('flask app secret key (blank for random)') or str(uuid.uuid4())

	AWS_BUCKET = prompt_need_response('s3 bucket')
	AWS_ACCESS_KEY = prompt_need_response('aws access key')
	AWS_SECRET_KEY = prompt_need_response('aws secret key')

	GH_ORG_NAME = prompt_need_response('github org name')
	GH_REPO_NAME = prompt_need_response('github repo name')

	print 'Get your org and repo ids from the GitHub API'
	GH_ORG = prompt_with_condition('github org id', lambda x: x.isdigit() ,'org id must be an int')
	GH_REPO = prompt_with_condition('github repo id', lambda x: x.isdigit() ,'repo id must be an int')

	print 'Create a new GitHub App at https://github.com/organizations/{}/settings/applications'.format(GH_ORG_NAME)
	GH_CLIENT_ID = prompt_with_condition('github client id', lambda x: len(x) == 20, 'client id must be 20 characters long')
	GH_SECRET = prompt_with_condition('github client secret', lambda x: len(x) == 40, 'client secret must be 40 characters long')
	
	_locals = locals()
	params = ['APP_NAME', 'SK', 'AWS_BUCKET', 'AWS_ACCESS_KEY', 'AWS_SECRET_KEY','GH_ORG', 'GH_REPO', 'GH_ORG_NAME', 'GH_REPO_NAME', 'GH_CLIENT_ID', 'GH_SECRET']
	return {param:_locals[param] for param in params}

def deploy(params):
	print 'Creating Heroku App'
	try:
		if params['APP_NAME']:
			output = subprocess.check_output(['heroku', 'create', params['APP_NAME']])
		else:
			output = subprocess.check_output(['heroku', 'create'])
		params['APP_NAME'] = re.match(r'Creating (.*)\.\.\.', output).group(1)
	except subprocess.CalledProcessError:
		sys.exit('heroku app creation failed!')
	config = map(lambda x: "{}={}".format(x[0], x[1]), params.items())

	print 'Writing Heroku Config Vars To .env'
	with open('.env', 'w') as f:
		f.write("\n".join(config))

	print 'Setting Heroku Config Vars'
	call_without_output(['heroku', 'config:set'] + config + ['--app', params['APP_NAME']])

	print 'Deploying to Heroku'
	git_remote = 'git@heroku.com:{}.git'.format(params['APP_NAME'])
	call_without_output(['git', 'remote', 'add', params['APP_NAME'], git_remote])
	call_without_output(['git', 'push', params['APP_NAME'], 'master'])

	message = "Set your GitHub App's Homepage URL to http://{}.herokuapp.com".format(params['APP_NAME'])
	print message
	prompt_with_condition('done? [y/n]', lambda x: x.lower() == 'y', message)

	message = "Set your GitHub App's Authorization Callback URL to http://{}.herokuapp.com/callback".format(params['APP_NAME'])
	print message
	prompt_with_condition('done? [y/n]', lambda x: x.lower() == 'y', message)

	print 'Launching App!'
	call_without_output(['heroku', 'ps:scale', 'web=1'])
	call_without_output(['heroku', 'apps:open', '--app', params['APP_NAME']])

	print 'App URL: http://{}.herokuapp.com'.format(params['APP_NAME'])

if __name__ == '__main__':
	try:
		clear()
		check_for_heroku()
		params = get_params()
		deploy(params)
	except KeyboardInterrupt:
		sys.exit('\nDeploy cancelled')
