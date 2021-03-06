# Responses.py
#
# Copyright 2012 Jeanluc Chasseriau <jeanluc@lo.cx>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from EnvimOutputs import *
from EnvimTools import *
from VimHelpers import *
from Helper import SimpleSingleton

log = logging.getLogger('envim')

# TODO: printing error using echoe()) in Handlers raise an error in abeans#processInput() without displaying the error

@SimpleSingleton
class ConnectionInfoHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("ConnectionInfo abort: "+codeDetailsString(code, details))

  def response(self, r):
    spid = ""
    if (r.pid): spid = str(r.pid)

    echo("server: "+r.implementation.name+" ("+r.version+") "+spid)

    configFile = getEnsimeConfigFile()
    if configFile == None:
      return

    config = ensimeConfigToPython(configFile)
    if config == None:
      return

    SwankRpc().projectInit(config)(InitProjectHandler())

@SimpleSingleton
class InitProjectHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("InitProject abort: "+codeDetailsString(code, details))

  def response(self, r):
    echo("Initializing project: "+str(r.project_name))

    for src in r.source_roots:
      log.debug("project source roots: "+src)

    State().initialized = True

@SimpleSingleton
class ShutdownServerHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("ShutdownServer abort: "+codeDetailsString(code, details))

  def response(self, r):
    echo("Ensime server is now off")

@SimpleSingleton
class TypecheckFileHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("TypecheckFile abort: "+codeDetailsString(code, details))

  def response(self, r):
    if r: echo("Typechecking in progress...")
    else: echoe("Typecheck file error")

    State().scalaNotes = []

@SimpleSingleton
class TypecheckAllHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("TypecheckAll abort: "+codeDetailsString(code, details))

  def response(self, r):
    if r: echo("Typechecking in progress...")
    else: echoe("Typecheck all error")

    State().scalaNotes = []

@SimpleSingleton
class SymbolAtPointHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("SymbolAtPoint abort: "+codeDetailsString(code, details))

  def response(self, symbolInfo):
    if not symbolInfo:
      #echo("No symbol here")
      PreviewOutput().set(["No symbol here"])
      return

    # Example:
    # Result for a val:
    # (:return (:ok (:name "toto" :type (:name "String" :type-id 1 :full-name "java.lang.String" :decl-as class) :decl-pos (:file "/Users/jeanluc/Source/vim/test_vim_ensime/src/main/scala/HelloWorld.scala" :offset 64) :owner-type-id 2)) 47)

    # Result for a method:
    #(:return (:ok (:name "println" :type (:name "(x: Any)Unit" :type-id 2 :arrow-type t :result-type (:name "Unit" :type-id 3 :full-name "scala.Unit" :decl-as class) :param-sections ((:params (("x" (:name "Any" :type-id 1 :full-name "scala.Any" :decl-as class)))))) :is-callable t :owner-type-id 4)) 45)

    # Fields may be defined depending on the type we are accessing

    out = symbolInfo.name + ' : ' + symbolInfo.type.name

    decl_as = ''
    if hasattr(symbolInfo.type, 'decl_as'):
      decl_as = symbolInfo.type.decl_as

    full_name = ''
    if hasattr(symbolInfo.type, 'full_name'):
      full_name = symbolInfo.type.full_name

    if decl_as != '' or full_name != '':
      out += ' (' + decl_as + ' ' + full_name + ')'

    log.debug("SymbolAtPointHandler.response: %s", out)

    #echo(out)
    PreviewOutput().set([out])

@SimpleSingleton
class UsesOfSymbolAtPointHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("SymbolAtPoint abort: "+codeDetailsString(code, details))

  def response(self, rangePosList):
    if not rangePosList:
      echo("Symbol not used")
      qflist = []
    else:
      qflist = rangePosToQuickFixList(rangePosList)

    QuickFixOutput().set(qflist)
    QuickFixOutput().open()

@SimpleSingleton
class CompletionsHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("Completions abort: "+codeDetailsString(code, details))

  def response(self, completions):
    if not completions or not completions.has('completions'):
      echo("Empty completions")
      OmniOutput().continueMessages()
      return

    reBase = None
    if OmniOutput().getBase() != '':
      reBase = re.compile("^%s.*" % (OmniOutput().getBase()))

    isCallableToVim = {True: 'f', False: 'v'}

    log.debug("CompletionsHandler.response:")

    out = [{'word':completions.prefix}]
    for comp in completions.completions:
      if reBase != None and reBase.match(comp.name) == None: continue
      d = {}
      d['word'] = comp.name
      d['info'] = comp.type_sig
      if comp.has('is_callable'):
        d['kind'] = isCallableToVim[comp.is_callable]

      out.append(d)

    out = sorted(out, key=lambda d: d['word'])

    OmniOutput().setResults(out)

    OmniOutput().showCompletions()

@SimpleSingleton
class FormatSourceHandler(SwankCallHandler):

  def abort(self, code, details):
    echoe("FormatSource abort: "+codeDetailsString(code, details))

  def response(self, r):
    if not r:
      echoe("FormatSource file error")
      return

    cmds = [
      "call feedkeys('<cr>')",
      # @todo: we use feedkeys() in order to avoid loosing the syntax colors, simply 'e' should be enough (cf. #9)
      "call feedkeys(':e')"
    ]
    vimCommands(cmds)

    echo("FormatSource done")

