/* regex to avoid html tags (injection) */
htmlData = htmlData.replace(/<script.*>[\s\S]*.*[\s\S]*<\/script>/g,"");