echo "Building Tailwind CSS..."
bash .scripts/tailwind.sh
echo "Building package..."
uv build
echo "Github push?"
read -p "Do you want to push to Github? (y/n) " -n 1 -r
echo
DATE=$(date)
if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo "Enter commit message:"
  read message
  git add .
  git commit -m "Build $DATE: $message"
  git push
fi
echo "Done!"