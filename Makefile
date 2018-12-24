test:
		@find . -not -iwholename '*.git*' -not -iwholename '*venv*' -type f -name *.py -exec python3 -m pylint {} \;

installhook:
		@cp -v pre-commit-hook .git/hooks/pre-commit
		@chmod +x .git/hooks/pre-commit
