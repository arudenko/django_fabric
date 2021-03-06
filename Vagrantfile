# -*- mode: ruby -*-
# vi: set ft=ruby :
def local_cache(box_name)
  cache_dir = File.join(File.expand_path("~/.vagrant"),
                        'cache',
                        'apt',
                        box_name)
  partial_dir = File.join(cache_dir, 'partial')
  FileUtils.mkdir_p(partial_dir) unless File.exists? partial_dir
  cache_dir
end

def local_venv_cache(box_name)
  cache_dir = File.join(File.expand_path("~/.vagrant"),
                        'cache',
                        'venv',
                        box_name)
  partial_dir = File.join(cache_dir, 'partial')
  FileUtils.mkdir_p(partial_dir) unless File.exists? partial_dir
  cache_dir
end

Vagrant.configure("2") do |config|

  # Every Vagrant virtual environment requires a box to build off of.
  config.vm.box = "precise32"
  config.vm.hostname = "vagrant-Django.com"

  config.vm.box_url = "http://files.vagrantup.com/precise32.box"

  # Boot with a GUI so you can see the screen. (Default is headless)
  # config.vm.boot_mode = :gui

  # Assign this VM to a host-only network IP, allowing you to access it
  # via the IP. Host-only networks can talk to the host machine as well as
  # any other machines on the same network, but cannot be accessed (through this
  # network interface) by any external networks.
  config.vm.network :private_network, ip: "88.88.88.88"

  cache_dir = local_cache(config.vm.box)
  venv_cache = local_venv_cache(config.vm.box)

  config.vm.synced_folder cache_dir, "/var/cache/apt/archives/"
  config.vm.synced_folder venv_cache, "/opt/r3/django/venv_cache"


end
