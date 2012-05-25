ActionController::Routing::Routes.draw do |map|
  map.pgcommunityauth '/pgcommunityauth', :controller => 'account', :action => 'pgcommunityauth'
end
