import re
from calibre.ebooks.BeautifulSoup import NavigableString

issue_page = 'jj883946.aspx' # January
# issue_page = 'jj891014.aspx' # February
# issue_page = 'jj991969.aspx' # March
# issue_page = 'dn166920.aspx' # April
# issue_page = 'dn198231.aspx' # May
# issue_page = 'dn201737.aspx' # June

issue_prefix = 'http://msdn.microsoft.com/en-us/magazine/'
cover_prefix = 'http://i.msdn.microsoft.com/'

class MsdnMagazine2013(BasicNewsRecipe):
    title = u'MSDN Magazine 2013'
    auto_cleanup = True
    auto_cleanup_keep = '//*[@class="FeatureTitle"]'
    remove_tags_before = { 'class' : 'MagazineStyle' }
    remove_tags_after  = { 'class' : 'MagazineStyle' }
    no_stylesheets = True
    publication_type = 'magazine'
    cover_url = cover_prefix + issue_page.replace('.aspx', '.cover_lrg(en-us,MSDN.10).jpg')
    
    def get_text(self, ele):
        title = ''

        for c in ele.contents:
            if isinstance(c, NavigableString):
                title = title + str(c)
            elif c.name == 'br':
                title = title + ': '
            else:
                title = title + self.get_text(c)
        
        return title.strip()
        
    def get_description(self, link):
        description = ''
    
        ele = link.nextSibling
        
        while ele:
            if isinstance(ele, NavigableString):
                description = description + str(ele)
            elif ele.name == 'br':
                description = description + ' '

            ele = ele.nextSibling
    
        return description.strip()
    
    def parse_index(self):
        soup = self.index_to_soup(issue_prefix + issue_page)
        
        self.title = soup.html.head.title.string.strip()
        
        mainContent = soup.find('div', { 'id' : "MainContent" })

        articles_dict = {}
        article_list = []
        
        for link in mainContent.findAll('a'):
            if link.img:
                continue
        
            href = link['href']
            if href == issue_page:
                continue
            
            if not re.match(r"\w\w\d+\.aspx", href):
                continue
            
            title = self.get_text(link)
            
            a = articles_dict.get(href)
            if a:
                old_title = a['title']
                if not old_title.endswith(':'):
                    old_title = old_title + ':'

                a['title'] = old_title + ' ' + title
            else:
                a = { 'title' : title, 'url' : issue_prefix + href.replace('.aspx', '(printer).aspx') }
                article_list.append(a)
                articles_dict[href] = a
                
            if link.parent.name == 'p':
                a['description'] = self.get_description(link)
            elif link.parent.name == 'strong' and len(link.contents) > 1:
                a['description'] = self.get_description(link.parent)

        return [('Default', article_list)]
        
    def postprocess_html(self, soup, first_fetch):
        for link in soup.findAll('a'):
            s = link.nextSibling

            if not (s and isinstance(s, NavigableString)):
                continue

            text = ' [ ' + link['href']
            if not s.startswith(text):
                continue
            
            index = s.find(' ] ', len(text)) + 3
            if index > 0:
                s.replaceWith(s[index:])

        return soup