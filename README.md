# Git Openl - A Git Extension for Openl
### Supported platforms
| Windows | macOS | linux
| :---- | :------ | :----
### Supported file formats
| 'xls'| 'xlsx'
| :--- | :----

# Getting started
### Installation
### Windows
You can install the Git Openl client on Windows, using the pre-compiled binary installer.

This repository can also be built-from-source using Python and PyInstaller.

Git Openl requires a global installation once per-machine. 
#### After running the openl-setup.exe this can be done by
running:

```
C:\Developer>git openl install
```

Alternatively, initialise Git Openl locally (per repository), using the --local option, inside the root folder of your repository’s local working copy:

```
C:\Developer>git openl install --local
```

#### Manual installation of exe files
Please, take the git-openl and git-openl-diff exe files, put it together to the temporary folder.
Then add this folder to PATH environment variable. Also comparison_url parameter must exists: by adding the variable called WebstudioPath or you need to change the git-openl.config after installation commands.
Then steps are the same:
```
C:\Developer>git openl install
```
AND/OR
```
C:\Developer>git openl install --local
```
## Customization
After installing depending on mode (global,local) there is created file called git-openl.config in the same folder as .gitconfig file
E.g, in windows 10 with global option it will be:
```
C:\Users\<username>\git-openl.config
```

If local mode was chosen:

```
../<project folder>/.git/git-openl.config
```
This file contains options for the plugin

| Name of property  | Value  | Description  |
|---|---|---|
| comparison_url  | http://localhost:8080/webstudio/web/public/compare/xls  |  URL for comparison the excel files |

By default this value is empty in Windows in config file, because the path is configured by installer and stored in environment - WebstudioPath in HKLU.
Local settings are preferable then global

### Uninstall
The same steps can be used for uninstalling the plugin.
#### Global
```
C:\Developer>git openl uninstall
```
#### Locally
```
C:\Developer>git openl uninstall --local
```

### MacOS/Linux
Please, take the corresponding executable files and install.sh script as example,
change the paths in script for yours and then run it.