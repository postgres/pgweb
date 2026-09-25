var repodata = {{json|safe}};
var supported_versions = [{{supported_versions}}];

/* Distributions in the order they are listed, keyed by platform prefix */
const distributions = [
    ['EL', 'RHEL / Rocky Linux / AlmaLinux / OL'],
    ['F', 'Fedora'],
    ['AL', 'Amazon Linux'],
];

function sortNumeric(a,b) {
   return a-b;
}

/* Compare dotted versions ("10.2", "9.8") newest first */
function sortVersionDesc(a, b) {
    const x = a.split('.').map(Number);
    const y = b.split('.').map(Number);
    for (let i = 0; i < Math.max(x.length, y.length); i++) {
        if ((x[i] || 0) != (y[i] || 0))
            return (y[i] || 0) - (x[i] || 0);
    }
    return 0;
}

/* "EL-10.2" -> ["EL", "10.2"] */
function split_platform(plat) {
    const i = plat.indexOf('-');
    return [plat.substring(0, i), plat.substring(i + 1)];
}

function get_major(plat) {
    return parseInt(split_platform(plat)[1]);
}

/* Platforms pinned to a minor release, like EL-10.2 */
function is_minor_platform(plat) {
    return split_platform(plat)[1].includes('.');
}

function get_rpm_prefix(plat) {
   if (plat.startsWith('EL-'))
       return 'redhat';
    else if (plat.startsWith('F-'))
	return 'fedora';
    else if (plat.startsWith('AL-'))
	return 'amazonlinux';
    return 'unknown';
}

function get_installer(plat) {
    if (plat.startsWith('F-') || plat.startsWith('AL-'))
	return 'dnf';
    else if (plat.startsWith('EL-')) {
	if (get_major(plat) >= 8)
	    return 'dnf';
    }
    return 'yum';
}

function disable_module_on(plat) {
    if (plat.startsWith('EL-')) {
	if (get_major(plat) == 8)
	    return true;
    }
    return false;
}

function uses_systemd(plat) {
    if (plat.startsWith('EL-')) {
	if (get_major(plat) < 7)
	    return false;
    }
    return true;
}

function get_arch_text(arch) {
    if (arch == 'aarch64')
	return 'aarch64 (arm64)';
    return arch;
}

/* Only offer platforms that have at least one supported PostgreSQL version */
function has_supported_versions(plat) {
    return repodata['platforms'][plat].some(a => a['versions'].some(v => supported_versions.includes(parseInt(v))));
}

function get_platforms(dist, minor) {
    return Object.keys(repodata['platforms'])
        .filter(p => split_platform(p)[0] === dist && is_minor_platform(p) === minor && has_supported_versions(p))
        .sort((a, b) => sortVersionDesc(split_platform(a)[1], split_platform(b)[1]));
}

function clear_options(box) {
  while (box.options.length > 0) {
    box.options.remove(0);
  }
}

function add_option(box, text, value) {
  const opt = document.createElement('option');
  opt.text = text;
  opt.value = value;
  box.add(opt);
}

window.onload = function() {
  const distbox = document.getElementById('distribution');
  const dists = distributions.filter(d => get_platforms(d[0], false).length > 0);

  /* Platforms from distributions we don't have a name for yet */
  for (const p of Object.keys(repodata['platforms'])) {
    const d = split_platform(p)[0];
    if (!dists.some(x => x[0] === d) && get_platforms(d, false).length > 0)
      dists.push([d, d]);
  }

  add_option(distbox, '* Select your distribution', '-1');
  for (const d of dists) {
    add_option(distbox, d[1], d[0]);
  }

  distChanged();
}

function distChanged() {
  const dist = document.getElementById('distribution').value;
  const minorbox = document.getElementById('minor-pin');
  const hasminors = dist !== '-1' && get_platforms(dist, true).length > 0;

  minorbox.classList.toggle('d-none', !hasminors);
  if (!hasminors)
    document.getElementById('minor').checked = false;

  minorChanged();
}

function minorChanged() {
  const dist = document.getElementById('distribution').value;
  const minor = document.getElementById('minor').checked;
  const platbox = document.getElementById('platform');

  clear_options(platbox);

  if (!dist || dist === "-1") {
    platChanged();
    return;
  }

  /* "(latest)" tells the rolling majors apart from the pinned minors */
  const hasminors = get_platforms(dist, true).length > 0;
  const plats = get_platforms(dist, minor);

  if (plats.length > 1)
    add_option(platbox, '* Select your distribution version', '-1');
  for (const p of plats) {
    let text = split_platform(p)[1];
    if (minor)
      text += ' (only)';
    else if (hasminors)
      text += ' (latest)';
    add_option(platbox, text, p);
  }

  platChanged();
}

function platChanged() {
  const plat = document.getElementById('platform').value;
  const archbox = document.getElementById('arch');

  clear_options(archbox);

  if (!plat || plat === "-1") {
    archChanged();
    return;
  }

  const archs = repodata['platforms'][plat].sort((a, b) => a['arch'].localeCompare(b['arch']));

  if (archs.length > 1)
    add_option(archbox, '* Select your architecture', '-1');
  for (const a of archs) {
    add_option(archbox, get_arch_text(a['arch']), a['arch']);
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

  for (const a in versions.sort(sortNumeric).reverse()) {
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
     document.getElementById('copy-btn-root').style.display = 'none';
     scriptBox.innerHTML = 'Select distribution, version, architecture and PostgreSQL version above';
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
  document.getElementById('copy-btn-root').style.display = 'block';
}

/* Event handlers */
function setupHandlers() {
    document.getElementById('copy-btn').addEventListener('click', function () {
        copyScript(this, 'script-box');
    });
    document.getElementById('copy-btn-root').addEventListener('click', function () {
        copyScript(this, 'script-box', true);
    });
    document.getElementById('version').addEventListener('change', verChanged);
    document.getElementById('distribution').addEventListener('change', distChanged);
    document.getElementById('minor').addEventListener('change', minorChanged);
    document.getElementById('platform').addEventListener('change', platChanged);
    document.getElementById('arch').addEventListener('change', archChanged);
}

document.addEventListener("DOMContentLoaded", setupHandlers);
