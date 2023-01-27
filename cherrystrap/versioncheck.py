# This file is sourced from the Headphones Project
# https://github.com/rembo10/headphones/blob/main/headphones/versioncheck.py

import re
import os
import tarfile
import platform
import subprocess
import cherrystrap
import simplejson as json
from urllib.request import urlopen

from cherrystrap import logger
import appfiles

def runGit(args):

    if cherrystrap.GIT_PATH:
        git_locations = ['"' + cherrystrap.GIT_PATH + '"']
    else:
        git_locations = ['git']

    if platform.system().lower() == 'darwin':
        git_locations.append('/usr/local/git/bin/git')

    output = err = None

    for cur_git in git_locations:
        cmd = cur_git + ' ' + args

        try:
            logger.debug('Trying to execute: "' + cmd + '" with shell in ' + cherrystrap.PROG_DIR)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=cherrystrap.PROG_DIR)
            output, err = p.communicate()
            output = output.decode('utf-8').strip()

            logger.debug('Git output: ' + output)
        except OSError:
            logger.debug('Command failed: %s', cmd)
            continue

        if 'not found' in output or "not recognized as an internal or external command" in output:
            logger.debug('Unable to find git with command ' + cmd)
            output = None
        elif 'fatal:' in output or err:
            logger.error('Git returned bad info. Are you sure this is a git installation?')
            output = None
        elif output:
            break

    return (output, err)


def getVersion():

    # This first statement will always fail.
    if cherrystrap.GIT_UPSTREAM.startswith('win32build'):
        cherrystrap.INSTALL_TYPE = 'win'

        # Don't have a way to update exe yet, but don't want to set VERSION to None
        return 'Windows Install', 'main'

    elif os.path.isdir(os.path.join(cherrystrap.PROG_DIR, '.git')):

        cherrystrap.INSTALL_TYPE = 'git'
        output, err = runGit('rev-parse HEAD')

        if not output:
            logger.error('Couldn\'t find latest installed version.')
            cur_commit_hash = None

        cur_commit_hash = str(output)

        if not re.match('^[a-z0-9]+$', cur_commit_hash):
            logger.error('Output doesn\'t look like a hash, not using it')
            cur_commit_hash = None

        if cherrystrap.GIT_OVERRIDE and appfiles.GIT_BRANCH:
            branch_name = appfiles.GIT_BRANCH

        else:
            branch_name, err = runGit('rev-parse --abbrev-ref HEAD')
            branch_name = branch_name

            if not branch_name and appfiles.GIT_BRANCH:
                logger.error('Could not retrieve branch name from git. Falling back to %s' % appfiles.GIT_BRANCH)
                branch_name = appfiles.GIT_BRANCH
            if not branch_name:
                logger.error('Could not retrieve branch name from git. Defaulting to main')
                branch_name = 'main'

        return cur_commit_hash, branch_name

    else:

        cherrystrap.INSTALL_TYPE = 'source'

        version_file = os.path.join(cherrystrap.PROG_DIR, 'version.txt')

        if not os.path.isfile(version_file):
            return None, 'main'

        with open(version_file, 'r') as f:
            current_version = f.read().strip(' \n\r')

        if current_version:
            return current_version, appfiles.GIT_BRANCH
        else:
            return None, 'main'


def checkGithub():
    cherrystrap.COMMITS_BEHIND = 0

    # Get the latest version available from github
    logger.info('Retrieving latest version information from GitHub')
    url = 'https://api.github.com/repos/%s/%s/commits/%s' % (appfiles.GIT_USER, appfiles.GIT_REPO, appfiles.GIT_BRANCH)
    try:
        result = urlopen(url).read()
        version = json.JSONDecoder().decode(result)
    except Exception as e:
        logger.warn('Could not get the latest version from GitHub. Are you running a local development version?: %s' % e)
        return cherrystrap.GIT_LOCAL

    cherrystrap.GIT_UPSTREAM = version['sha']
    logger.debug("Latest version is %s" % cherrystrap.GIT_UPSTREAM)

    # See how many commits behind we are
    if not cherrystrap.GIT_LOCAL:
        logger.info('You are running an unknown version of %s. Run the updater to identify your version' % cherrystrap.APP_NAME)
        return cherrystrap.GIT_UPSTREAM

    if cherrystrap.GIT_UPSTREAM == cherrystrap.GIT_LOCAL:
        logger.info('%s is up to date' % cherrystrap.APP_NAME)
        return cherrystrap.GIT_UPSTREAM

    logger.info('Comparing currently installed version with latest GitHub version')
    url = 'https://api.github.com/repos/%s/%s/compare/%s...%s' % (appfiles.GIT_USER, appfiles.GIT_REPO, cherrystrap.GIT_UPSTREAM, cherrystrap.GIT_LOCAL)
    try:
        result = urlopen(url).read()
        commits = json.JSONDecoder().decode(result)
    except:
        logger.warn('Could not get commits behind from GitHub.')
        return cherrystrap.GIT_UPSTREAM

    try:
        cherrystrap.COMMITS_BEHIND = int(commits['behind_by'])
        logger.debug("In total, %d commits behind" % cherrystrap.COMMITS_BEHIND)
    except KeyError:
        logger.info('Cannot compare versions. Are you running a local development version?')
        cherrystrap.COMMITS_BEHIND = 0

    if cherrystrap.COMMITS_BEHIND > 0:
        logger.info('New version is available. You are %s commits behind' % cherrystrap.COMMITS_BEHIND)
    elif cherrystrap.COMMITS_BEHIND == 0:
        logger.info('%s is up to date' % cherrystrap.APP_NAME)

    return cherrystrap.GIT_UPSTREAM


def update():
    if cherrystrap.INSTALL_TYPE == 'win':
        logger.info('Windows .exe updating not supported yet.')

    elif cherrystrap.INSTALL_TYPE == 'git':
        output, err = runGit('pull origin ' + appfiles.GIT_BRANCH)

        if not output:
            logger.error('Couldn\'t download latest version')

        for line in output.split('\n'):

            if 'Already up-to-date.' in line:
                logger.info('No update available, not updating')
                logger.info('Output: ' + str(output))
            elif line.endswith('Aborting.'):
                logger.error('Unable to update from git: ' + line)
                logger.info('Output: ' + str(output))

    else:
        tar_download_url = 'https://github.com/%s/%s/tarball/%s' % (appfiles.GIT_USER, appfiles.GIT_REPO, appfiles.GIT_BRANCH)
        update_dir = os.path.join(cherrystrap.PROG_DIR, 'update')
        version_path = os.path.join(cherrystrap.PROG_DIR, 'version.txt')

        logger.info('Downloading update from: ' + tar_download_url)
        data = urlopen(tar_download_url)

        if not data:
            logger.error("Unable to retrieve new version from '%s', can't update", tar_download_url)
            return

        download_name = appfiles.GIT_BRANCH + '-github'
        tar_download_path = os.path.join(cherrystrap.PROG_DIR, download_name)

        # Save tar to disk
        with open(tar_download_path, 'wb') as f:
            f.write(data)

        # Extract the tar to update folder
        logger.info('Extracting file: ' + tar_download_path)
        tar = tarfile.open(tar_download_path)
        tar.extractall(update_dir)
        tar.close()

        # Delete the tar.gz
        logger.info('Deleting file: ' + tar_download_path)
        os.remove(tar_download_path)

        # Find update dir name
        update_dir_contents = [x for x in os.listdir(update_dir) if os.path.isdir(os.path.join(update_dir, x))]
        if len(update_dir_contents) != 1:
            logger.error("Invalid update data, update failed: " + str(update_dir_contents))
            return
        content_dir = os.path.join(update_dir, update_dir_contents[0])

        # walk temp folder and move files to main folder
        for dirname, dirnames, filenames in os.walk(content_dir):
            dirname = dirname[len(content_dir) + 1:]
            for curfile in filenames:
                old_path = os.path.join(content_dir, dirname, curfile)
                new_path = os.path.join(cherrystrap.PROG_DIR, dirname, curfile)

                if os.path.isfile(new_path):
                    os.remove(new_path)
                os.renames(old_path, new_path)

        # Update version.txt
        try:
            with open(version_path, 'w') as f:
                f.write(str(cherrystrap.GIT_UPSTREAM))
        except IOError as e:
            logger.error(
                "Unable to write current version to version.txt, update not complete: %s",
                e
            )
            return
