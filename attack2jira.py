from attackcti import attack_client
import json, sys, argparse, traceback
from getpass import getpass
from lib.jirahandler import JiraHandler
import re

class Attack2Jira:

    jirahandler = None

    def __init__(self, url, username, password):

        jirahandler = JiraHandler(url, username, password)
        self.jirahandler = jirahandler

    def get_attack_techniques(self):

        try:
            print ("[*] Obtaining ATT&CK's techniques...")
            client = attack_client()
            all_enterprise = client.get_enterprise()
            techniques = []
            for technique in all_enterprise['techniques']:
                techniques.append(json.loads(technique.serialize()))

            print ("[!] Done!")
            return techniques

        except:
            traceback.print_exc(file=sys.stdout)
            print ("[!] Error connecting to Att&ck's API !")
            return


    def create_attack_techniques(self):

        techniques = self.get_attack_techniques()
        jiraclient = self.jirahandler

        print ("[*] Creating Jira issues for ATT&CK's techniques...")
        for technique in techniques:
            try:

                custom_fields=self.jirahandler.get_custom_fields()

                name = technique['name']
                id = technique['external_references'][0]['external_id']
                url = technique['external_references'][0]['url']
                tactic = technique['kill_chain_phases'][0]['phase_name']
                description = technique['description']

                issue_dict = {
                    "fields": {
                        "project": {"key": "ATTACK"},
                        "summary":  name + " (" + id + ")",
                        "description": description,
                        "issuetype": {"name": "Task"},
                        custom_fields['tactic']: {'value': tactic},
                        custom_fields['maturity']: {'value':'Not Tracked'},
                        custom_fields['url']: url,
                        # "customfield_11050": "Value that we're putting into a Free Text Field."
                    }
                }
                jiraclient.create_issue(issue_dict,id)

            except Exception as ex:
                print ("\t[*] Could not create ticket for " + id)
                print(ex)
                sys.exit()

        print ("[*] Done!")



    def generate_json_layer(self):
        VERSION = "2.1"
        NAME = "example"
        DESCRIPTION = "Attack2Jira"
        DOMAIN = "mitre-enterprise"
        GRADIENT = {
                "colors": [
                    "#DCDCDC",
                    "#03ad03"],
            }

        layer_json = {
            "domain": DOMAIN,
            "name": NAME,
            "description": DESCRIPTION,
            "gradient": GRADIENT,
            "version": VERSION,
            "hideDisabled": True,
            "techniques": [ ]
        }

        res_dict=self.jirahandler.get_technique_maturity()
        for key in res_dict.keys():
            enabled = True
            #print (key +" "+ res_dict[key]['value'])
            #Extract the Technique ID from the title of each JIRA ticket
            if res_dict[key]['value'] == "Not Tracked":
                enabled=False
                color = "#DCDCDC"
            elif res_dict[key]['value'] == "Initial":
                color = "#e1fce1"
            elif res_dict[key]['value'] == "Defined":
                color = "#81fc81"
            elif res_dict[key]['value'] == "Resilient":
                color = "#49fc49"
            elif res_dict[key]['value'] == "Optimized":
                color = "#03ad03"
            
            technique = {
            "techniqueID": key,
            "enabled": enabled,
            "color": color
            }
            layer_json["techniques"].append(technique)

        print ("[*] Outputting a JSON layer!")
        with open('attack2jira.json', 'w', encoding='utf-8') as f:
            json.dump(layer_json, f, ensure_ascii=False, indent=4)
        

    def set_up_jira_automated(self):

        self.jirahandler.create_project()
        self.jirahandler.create_custom_fields()
        self.jirahandler.add_custom_field_options()
        self.jirahandler.add_custom_field_to_screen_tab()
        self.jirahandler.hide_unwanted_fields()
        self.create_attack_techniques()


def main():

    parser = argparse.ArgumentParser()#(description='Process some integers.')
    parser.add_argument('-url', dest = 'url', type=str, help= 'URL of Jira instance', default="")
    parser.add_argument('-u', dest = 'user', type=str, help='Username', default="")
    parser.add_argument('-a', dest='action', type=str, default="", help='action to execute. Two supported: \'create\' and \'createjsonlayer\'')
    results = parser.parse_args()

    url= results.url
    user= results.user
    action = results.action

    if (url and user and action):
        pswd = getpass('Jira API Token for '+user+":")

        if (action == "create"):
            attack2jira = Attack2Jira(url, user, pswd)
            attack2jira.set_up_jira_automated()

        if (action == "createjsonlayer"):
            attack2jira = Attack2Jira(url, user, pswd)
            attack2jira.generate_json_layer()
    else:
        parser.print_help()

if __name__ == '__main__':

    try:
       main()

    except KeyboardInterrupt:
        print("\n")
        print ("[!] Exiting attack2jira")
        sys.exit()