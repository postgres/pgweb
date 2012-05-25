require 'redmine'
require 'dispatcher'

Dispatcher.to_prepare do
  require_dependency 'account_controller'

  AccountController.send(:include, RedminePgcommunityauth::AccountControllerPatch)
end

Redmine::Plugin.register :redmine_pgcommunityauth do
  name 'Redmine Pgcommunityauth plugin'
  author 'Alex Shulgin <ash@commandprompt.com>'
  description ''
  version '0.0.1'

  settings :default => {}, :partial => 'settings/redmine_pgcommunityauth_settings'
end
