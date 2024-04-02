# $Source: /usr/local/cvs/scripts/deploy/bin/AbstractDeployer.py,v $
#
# Copyright (c) 1999-2004 OAT Systems, Inc.  All Rights Reserved.
#
# This software is the confidential and proprietary information
# (Confidential Information) of OAT Systems, Inc.  You shall not
# disclose or use Confidential Information without the express written
# agreement of OAT Systems, Inc.
#
#
# Author     : Chris Winters
# Version $Id: AbstractDeployer.py,v 1.7 2005/02/16 16:28:32 cwinters Exp $
#

import os
import replaceConfigVars
import log, utils


class AbstractDeployer:
    """Typically used as:
    deployer = SomeSubclassDeployer(config, dir)
    deployer.customHook()
    deployer.run()
    """

    # add verbose or log level to state?

    def __init__(self, configVars, directory, customFile):
        self.config = configVars
        self.dir = directory
        self.dorun = 1
        self.customFile = customFile

    def syscmd(self, cmd):
        """Run OS commands with @@ replacement, in cwd."""
        replaceConfigVars.sysExpandedCommand(self.config, cmd, self.dir)    

    def customHook(self):
        """Run customFile at srcdir, if it exists.
        
        config (a dict) and deployer be in scope
        
        deployer can be of type PackageDeployer, SqlDeployer, or other,
        depending on location where deploy.py resides.
        
        deployer.syscmd() will run OS commands with cwd = path,
        and with @@ replacement.
        """

        for f in [ self.customFile,
                   "deploy.py"]:     # deploy.py is deprecated
            if self.tryCustomHook(f):
                break

    def tryCustomHook(self, basename):

        filename = utils.pjoin(self.dir, basename)
        if os.path.exists(filename):
            log.summary("  running", utils.dropSuffix(filename))

            # This used to have own scope (with a copy of config), but now runs
            # in local scope to permit easier modification of things I haven't
            # anticipated

            deployer = self
            config = self.config

            execfile(filename) 
            return 1
        else:
            return 0


    def run(self):
        raise Exception, "Deployer.run() not implemented"

