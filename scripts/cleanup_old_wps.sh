#!/bin/bash
# Remove old parent WP files that have been broken down into sub-WPs

cd /workspaces/Ultimate_Kids_Curiousity_club/docs/work_packages

echo "Removing old parent WP files..."
rm -f WP1_Foundation.md
rm -f WP2_LLM_Service.md
rm -f WP6_Orchestrator.md
rm -f WP7_CLI.md
rm -f WP9_Dashboard.md
rm -f WP10_Website_Distribution.md

echo "Done! Remaining WP files:"
ls -1 WP*.md
