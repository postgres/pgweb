require 'base64'
require 'openssl' # aes gem doesn't let us disable PKCS#5 padding

module RedminePgcommunityauth
  module AccountControllerPatch
    unloadable

    class AuthTokenExpiredError < RuntimeError; end
    class InvalidAuthTokenError < RuntimeError; end

    def self.included(base)
      base.class_eval do
        alias_method_chain :login,  :pgcommunityauth
        alias_method_chain :logout, :pgcommunityauth
      end
    end

    def login_with_pgcommunityauth
      redirect_to pgcommunityauth_login_url
    end

    def logout_with_pgcommunityauth
      logout_user
      redirect_to pgcommunityauth_logout_url
    end

    # GET /pgcommunityauth
    def pgcommunityauth
      if params[:s] == 'logout'
        flash[:notice] = "Successfully logged out from PG community sites."
        return
      end

      data = (params[:d] || "").tr('-_', '+/')
      iv   = (params[:i] || "").tr('-_', '+/')

      qs = aes_decrypt(data, iv).rstrip
      auth = Rack::Utils.parse_query(qs)

      # check auth hash for mandatory keys
      raise InvalidAuthTokenError.new unless %w(t u f l e).all?{ |x| auth.keys.include?(x) }

      # check auth token timestamp: issued 10 seconds ago or less
      raise AuthTokenExpiredError.new unless Time.now.to_i <= auth['t'].to_i + 10

      # prepare attrs for create or update
      attrs = {
        :firstname => auth['f'],
        :lastname => auth['l'],
        :mail => auth['e']
      }
      if user = User.find_by_login(auth['u'])
        user.update_attributes! attrs
      else
        user = User.new(attrs)
        # can't pass protected attr in new/create
        user.login = auth['u']
        user.save!
      end

      params[:back_url] = auth['su'] || pgcommunityauth_settings[:default_url]
      successful_authentication(user)
    rescue OpenSSL::Cipher::CipherError
      flash[:error] = "Invalid PG communityauth message received."
    rescue InvalidAuthTokenError
      flash[:error] = "Invalid PG communityauth token received."
    rescue AuthTokenExpiredError
      flash[:error] = "PG community auth token expired."
    end

    private

    def pgcommunityauth_settings
      Setting['plugin_redmine_pgcommunityauth']
    end

    def pgcommunityauth_base_url
      "https://www.postgresql.org/account/auth/#{pgcommunityauth_settings[:authsite_id]}"
    end

    def pgcommunityauth_login_url
      "#{pgcommunityauth_base_url}/"
    end

    def pgcommunityauth_logout_url
      "#{pgcommunityauth_base_url}/logout/"
    end

    def aes_decrypt(data, iv)
      key = Base64.decode64(pgcommunityauth_settings[:cipher_key])

      cipher = OpenSSL::Cipher.new("AES-#{key.size*8}-CBC")
      cipher.decrypt

      # this is the key point here, otherwise we could use
      # AES.decrypt()
      cipher.padding = 0

      cipher.key = key
      cipher.iv  = Base64.decode64(iv)
      cipher.update(Base64.decode64(data)) + cipher.final
    end
  end
end
