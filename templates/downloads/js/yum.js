var repodata = {{json|safe}};
var supported_versions = [{{supported_versions}}];

function sortNumeric(a,b) {
   return a-b;
}

function get_platform_name(plat, ver) {
    if (plat == 'EL') {
        if (parseFloat(ver) <= 7)
	    return "Red Hat Enterprise, CentOS, Scientific or Oracle";
        else
	    return "Red Hat Enterprise, CentOS or Oracle";
    }
    else if (plat == 'F')
	return "Fedora";
    return "Undefined distribution";
}

function get_rpm_prefix(plat) {
   if (plat.startsWith('EL-'))
       return 'redhat';
    else if (plat.startsWith('F-'))
	return 'fedora';
    return 'unknown';
}

function get_installer(plat) {
    if (plat.startsWith('F-'))
	return 'dnf';
    else if (plat.startsWith('EL-')) {
	var a = plat.split('-');
	if (a[1] >= 8)
	    return 'dnf';
    }
    return 'yum';
}

function disable_module_on(plat) {
    if (plat.startsWith('EL-')) {
	var a = plat.split('-');
	if (a[1] >= 8)
	    return true;
    }
    return false;
}

function uses_systemd(plat) {
    if (plat.startsWith('EL-')) {
	var a = plat.split('-');
	if (a[1] < 7)
	    return false;
    }
    return true;
}

function get_platform_text(p) {
    var a = p.split('-');
    return get_platform_name(a[0], a[1]) + ' version ' + a[1];
}

window.onload = function() {
   for (var p in supported_versions) {
      var opt = document.createElement('option');
      opt.text = supported_versions[p];
      document.getElementById('version').add(opt);
   }

   loadPlatforms();
   archChanged();
}

function verChanged() {
    /* Just update like the architecture changed */
    archChanged();
}

function loadPlatforms() {
   var platbox = document.getElementById('platform');

   while (platbox.options.length > 0) {
      platbox.options.remove(0);
   }
   var opt = document.createElement('option');
   opt.text = '* Select your platform';
   opt.value = -1;
   platbox.add(opt);

   platkeys = Object.keys(repodata['platforms']).sort();
   for (var pp in platkeys) {
      var opt = document.createElement('option');
      opt.text = get_platform_text(platkeys[pp]);
      opt.value = platkeys[pp];
      platbox.add(opt);
   }

   platChanged();
}

function platChanged() {
   var plat = document.getElementById('platform').value;
   var archbox = document.getElementById('arch');

   while (archbox.options.length > 0) {
      archbox.options.remove(0);
   }

   if (plat == -1) {
      archChanged();
      return;
   }

   for (a in repodata['platforms'][plat].sort().reverse()) {
      var opt = document.createElement('option');
      opt.text = opt.value = repodata['platforms'][plat][a];
      archbox.add(opt);
   }

   archChanged();
}

function archChanged() {
   var ver = document.getElementById('version').value;
   var plat = document.getElementById('platform').value;
   var arch = document.getElementById('arch').value;
   var scriptBox = document.getElementById('script-box')

   if (!plat || plat == -1) {
      document.getElementById('copy-btn').style.display = 'none';
      scriptBox.innerHTML = 'Select version and platform above';
      return;
   }

   var pinfo = repodata['platforms'][plat];
   var shortver = ver.replace('.', '');

   var url = 'https://download.postgresql.org/pub/repos/yum/reporpms/' + plat + '-' + arch + '/pgdg-' + get_rpm_prefix(plat) +'-repo-latest.noarch.rpm';

   var installer = get_installer(plat);
   scriptBox.innerHTML = '# Install the repository RPM:\n';
   scriptBox.innerHTML += 'sudo ' + installer + ' install -y ' + url + '\n\n';

   if (disable_module_on(plat)) {
      scriptBox.innerHTML += '# Disable the built-in PostgreSQL module:\n';
      scriptBox.innerHTML += 'sudo dnf -qy module disable postgresql\n\n';
   }

   scriptBox.innerHTML += '# Install PostgreSQL:\n';
   scriptBox.innerHTML += 'sudo ' + installer + ' install -y postgresql' + shortver + '-server\n\n';

   scriptBox.innerHTML += '# Optionally initialize the database and enable automatic start:\n';
   if (uses_systemd(plat)) {
       var setupcmd = 'postgresql-' + shortver + '-setup';
       if (ver < 10) {
	       setupcmd = 'postgresql' + shortver + '-setup';
       }
       scriptBox.innerHTML += 'sudo /usr/pgsql-' + ver + '/bin/' + setupcmd + ' initdb\nsudo systemctl enable postgresql-' + ver + '\nsudo systemctl start postgresql-' + ver;
   }
   else {
       scriptBox.innerHTML += 'sudo service postgresql-' + ver + ' initdb\nsudo chkconfig postgresql-' + ver + ' on\nsudo service postgresql-' + ver + ' start';
   }

   document.getElementById('copy-btn').style.display = 'block';
}

/* Event handlers */
function setupHandlers() {
    document.getElementById('copy-btn').addEventListener('click', function () {
        copyScript(this, 'script-box');
    });
    document.getElementById('version').addEventListener('change', verChanged);
    document.getElementById('platform').addEventListener('change', platChanged);
    document.getElementById('arch').addEventListener('change', archChanged);
}

document.addEventListener("DOMContentLoaded", setupHandlers);
