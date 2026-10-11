import shutil
import subprocess
import unittest
from pathlib import Path


class BrowserPreferenceTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "JavaScript tests require Node.js")
    def test_validated_preferences_and_storage_failure(self):
        subprocess.run(["node", "--input-type=module", "-e", r'''
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import assert from 'node:assert/strict';
const source=readFileSync('webapp/app.js','utf8'),functions=source.slice(source.indexOf('function loadBrowserPreferences()'),source.indexOf('loadBrowserPreferences();'));
for(const success of [false,true]){
 const nodes=new Map([['preview-audio',{checked:true}],['speech-language',{value:'en-US'}],['preferences-status',{textContent:''}]]),context={byId:id=>nodes.get(id),PREFERENCES_KEY:'test',localStorage:{getItem:()=>JSON.stringify({previewAudio:false,speechLanguage:'unsupported'}),setItem(){if(!success)throw Error('Synthetic storage failure');}}};
 runInNewContext(functions,context);context.loadBrowserPreferences();assert.equal(nodes.get('preview-audio').checked,false);assert.equal(nodes.get('speech-language').value,'en-US');context.saveBrowserPreferences();assert.match(nodes.get('preferences-status').textContent,success?/Saved on this browser/:/this session only/);
}
'''], check=True, cwd=Path(__file__).resolve().parents[1])
