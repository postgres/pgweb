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
	    return "Red Hat Enterprise, Rocky, AlmaLinux or Oracle";
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
    const a = p.split('-');
    return get_platform_name(a[0], a[1]) + ' version ' + a[1];
}

window.onload = function() {
  const platbox = document.getElementById('platform');
  const platkeys = Object.keys(repodata['platforms']).sort();

  let opt = document.createElement('option');
  opt.text = '* Select your platform';
  opt.value = "-1";
  platbox.add(opt);

  for (const pp in platkeys) {
    opt = document.createElement('option');
    opt.text = get_platform_text(platkeys[pp]);
    opt.value = platkeys[pp];
    platbox.add(opt);
  }

  platChanged()
}

function platChanged() {
  const plat = document.getElementById('platform').value;
  const archbox = document.getElementById('arch');

  while (archbox.options.length > 0) {
    archbox.options.remove(0);
  }

  if (!plat || plat === "-1") {
    archChanged();
    return;
  }

 let opt = document.createElement('option');
 opt.text = '* Select your architecture';
 opt.value = "-1";
 archbox.add(opt);

  for (const a in repodata['platforms'][plat].sort((a, b) => a['arch'].localeCompare(b['arch']))) {
     opt = document.createElement('option');
     opt.text = opt.value = repodata['platforms'][plat][a]['arch'];
     archbox.add(opt);
  }

  archChanged();
}

function archChanged() {
  const plat = document.getElementById('platform').value;
  const arch = document.getElementById('arch').value;
  const verbox = document.getElementById('version');

  while (verbox.options.length > 0) {
    verbox.options.remove(0);
  }

  if (!arch || arch === "-1") {
    verChanged();
    return;
  }

 let opt = document.createElement('option');
 opt.text = '* Select your required PostgreSQL version';
 opt.value = "-1";
 verbox.add(opt);

 let versions = []
 for (const a in repodata['platforms'][plat]) {
   if (repodata['platforms'][plat][a]['arch'] === arch) {
     versions = repodata['platforms'][plat][a]['versions']
     break
   }
 }

  for (const a in versions.sort()) {
    if (supported_versions.includes(parseInt(versions[a]))) {
      opt = document.createElement('option');
      opt.text = opt.value = versions[a];
      verbox.add(opt);
    }
  }

  verChanged();
}

function verChanged() {
  var ver = document.getElementById('version').value;
  var plat = document.getElementById('platform').value;
  var arch = document.getElementById('arch').value;
  var scriptBox = document.getElementById('script-box')

  if (!ver || ver === "-1") {
     document.getElementById('copy-btn').style.display = 'none';
     scriptBox.innerHTML = 'Select platform, architecture, and version above';
     return;
  }

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
