def update_coverage(args):
  repo_name = args.get('repo_name')
  if not repo_name:
    return jsonify({'status': 'no repo name'})
  bot = bots.get(repo_name)
  storage = storages.get(repo_name)
  if bot:
    if not args['pull_request_id'].isdigit():
      # args['pull_request_id'] is the branch name
      if storage:
        commit = args.pop('commit_id')
        if commit:
          value = storage.get(args['pull_request_id'], {})
          value[commit] = args
          value['current'] = args
          storage.set(args['pull_request_id'], value)
      try:
        args['pull_request_id'] = bot.get_pr_by_branch(args['pull_request_id']).number
      except:
        return jsonify({'status': 'no such pull request'})
    url = url_for('go_view', object_key=args.get('object_key', ''), _external=True)
    if bot.process_hook(int(args['pull_request_id']), url, args, storage):
      return jsonify({'status': 'success'})
    else:
      return jsonify({'status': 'restarting'})
  return jsonify({'status': 'no bot credentials'})

