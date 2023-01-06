let theme = 'light';
if (localStorage.getItem('theme')) {
  if (localStorage.getItem('theme') === 'dark') {
    theme = 'dark';
    document.documentElement.setAttribute('data-theme', 'dark');
  }
} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  theme = 'dark';
  document.documentElement.setAttribute('data-theme', 'dark');
}