var repodata = {{json|safe}};
var supported_versions = [{{supported_versions}}];

function sortNumeric(a,b) {
   return a-b;
}

window.onload = function() {
   versions = Object.keys(repodata['reporpms']).sort(sortNumeric).reverse();
   for (var p in versions) {
      if (supported_versions.indexOf(Number(versions[p])) < 0)
	  continue;

      var opt = document.createElement('option');
      opt.text = versions[p];
      document.getElementById('version').add(opt);
   }

   verChanged();
}

function verChanged() {
   var newver = document.getElementById('version').value;
   var platbox = document.getElementById('platform');

   while (platbox.options.length > 0) {
      platbox.options.remove(0);
   }
   var opt = document.createElement('option');
   opt.text = '* Select your platform';
   opt.value = -1;
   platbox.add(opt);

   plats = Object.keys(repodata['reporpms'][newver]).sort(
       function(a,b) {
	   return repodata['platforms'][a].s - repodata['platforms'][b].s;
       }
   );
   for (p in plats) {
      var opt = document.createElement('option');
      opt.text = repodata['platforms'][plats[p]].t;
      opt.value = plats[p];
      platbox.add(opt);
   }

   platChanged();
}

function platChanged() {
   var ver = document.getElementById('version').value;
   var plat = document.getElementById('platform').value;
   var archbox = document.getElementById('arch');

   while (archbox.options.length > 0) {
      archbox.options.remove(0);
   }

   if (plat == -1) {
      archChanged();
      return;
   }

   var platname = repodata['platforms'][plat].t;

   archs = Object.keys(repodata['reporpms'][ver][plat]).sort().reverse();
   for (a in archs) {
      var opt = document.createElement('option');
      opt.text = archs[a];
      opt.value = archs[a];
      archbox.add(opt);
   }

   archChanged();
}

function archChanged() {
   var ver = document.getElementById('version').value;
   var plat = document.getElementById('platform').value;
   var arch = document.getElementById('arch').value;

   if (plat == -1) {
      document.getElementById('reporpm').innerHTML = 'Select version and platform above';
      document.getElementById('clientpackage').innerHTML = 'Select version and platform above';
      document.getElementById('serverpackage').innerHTML = 'Select version and platform above';
      document.getElementById('initdb').innerHTML = 'Select version and platform above';
      return;
   }

   var pinfo = repodata['platforms'][plat];
   var shortver = ver.replace('.', '');

   var url = 'https://download.postgresql.org/pub/repos/yum/' + ver + '/' + pinfo['p'] + '-' + arch + '/pgdg-' + pinfo['f'] + shortver + '-' + ver + '-' + repodata['reporpms'][ver][plat][arch] + '.noarch.rpm';

   document.getElementById('reporpm').innerHTML = pinfo['i'] + ' install ' + url;
   document.getElementById('clientpackage').innerHTML = pinfo['i'] + ' install postgresql' + shortver;
   document.getElementById('serverpackage').innerHTML = pinfo['i'] + ' install postgresql' + shortver + '-server';
   if (pinfo.d) {
       document.getElementById('initdb').innerHTML = '/usr/pgsql-' + ver + '/bin/postgresql' + shortver + '-setup initdb<br/>systemctl enable postgresql-' + ver + '<br/>systemctl start postgresql-' + ver;
   }
   else {
       document.getElementById('initdb').innerHTML = 'service postgresql-' + ver + ' initdb<br/>chkconfig postgresql-' + ver + ' on<br/>service postgresql-' + ver + ' start';
   }
}
