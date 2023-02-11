pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'imagery')
gnome = import('gnome')

gnome.compile_resources('imagery',
  'imagery.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'imagery.in',
  output: 'imagery',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

imagery_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'mod.py',
  'start_page.py',
  'text_to_image_page.py',
  'image_to_image_page.py',
  'file.py',
  'model_files.py',
  'preferences.py',
  'settings_manager.py',
  'download_manager.py',
  'text_to_image_runner.py',
  'image_to_image_runner.py',
  'prompt_ideas.py'
]

install_data(imagery_sources, install_dir: moduledir)
