import re, urlparse, itertools
from calibre.ebooks.BeautifulSoup import NavigableString, Tag
from datetime import date

site_url = 'http://www.infoq.com/'
date_regexes = [
    r'Jan\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Feb\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Mar\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Apr\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'May\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Jun\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Jul\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Aug\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Sep\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Oct\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Nov\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'Dec\s+(?P<day>\d{2}),\s+(?P<year>\d{4})'
]

def parse_date(text):
    for i in xrange(len(date_regexes)):
        m = re.search(date_regexes[i], text)
        if not m: continue
        
        year = int(m.group('year'))
        month = i + 1
        day = int(m.group('day'))
        
        return date(year, month, day)

def get_text(tag):
    text = ''
    for c in tag.contents:
        if isinstance(c, NavigableString):
            text = text + str(c)
        else:
            text = text + get_text(c)
            
    return text.strip()
    
def find_by_class(tag, name, cls):
    for c in tag.findAll(name):
        c_cls = c.get('class')
        if not c_cls: continue
        if cls not in c_cls: continue
        
        yield c

section_texts = {}
section_item_classes = {
    'news': ['news_type_block'],
    'articles': ['news_type1', 'news_type2'],
    'interviews': ['news_type_video']
}
        
class InfoQ(BasicNewsRecipe):
    title = u'InfoQ'
    # auto_cleanup = True
    no_stylesheets = True
    
    keep_only_tags = [ { 'id': 'content' } ]
    
    remove_tags = [
        { 'id': 'noOfComments' },
        { 'class': 'share_this' },
        { 'class': 'article_page_right' }
    ]
    
    def get_items(self, section):
        print '>>> Retrieving items for section: ', section
    
        text_retrieved = False
        count = 0

        while True:
            print '>>> Loading items from ', count

            root = self.index_to_soup(site_url + section + '/' + str(count))
            content_div = root.find('div', { 'id': 'content' })
            
            if not text_retrieved:
                text_retrieved = True
                text = content_div.h2.string.strip()
                section_texts[section] = text
                print '>>> Text for section "' + section + '": ' + text
                
            for item_class in section_item_classes[section]:
                for item_div in find_by_class(content_div, 'div', item_class):
                    item = {}
                    link = item_div.h2.a
                    item['title'] = link.string.strip()
                    item['url'] = urlparse.urljoin(site_url, link['href'])
                    item['description'] = get_text(item_div.p)

                    author_span = item_div.find('span', { 'class': 'author' })
                    date_text = str(author_span.contents[-1])
                    item['date'] = parse_date(date_text)
                    
                    print '>>> Item parsed: ', item
                    
                    yield item
                    count = count + 1
    
    def parse_index(self):
        index = []
        
        dict = { 'news': 300, 'articles': 100, 'interviews': 30 }
        
        for section in dict:
            items = list(itertools.islice(self.get_items(section), 0, dict[section]))
            index.append((section_texts[section], items))

        return index
    
    def postprocess_html(self, soup, first_fetch):
        author_general = soup.find('span', { 'class': 'author_general' })
        author_general.em.extract()
    
        transcript_div = soup.find('div', { 'id': 'transcript' })
        if transcript_div: # that's an interview
            # get all <div class="qa" />
            qa_div_list = list(find_by_class(transcript_div, 'div', 'qa'))
            for qa_div in qa_div_list:
                qa_div.extract()
                
                # replace all <a class="question_link">...</a> with <strong>...</strong>
                question_link = qa_div.find('a', { 'class': 'question_link' })
                question_strong = Tag(soup, 'strong')
                question_strong.insert(0, question_link.string)
                question_link.replaceWith(question_strong)
            
            full_div = find_by_class(soup.find('div', { 'id': 'content' }), 'div', 'presentation_full').next()
            
            # clean the <h1 />
            full_div.h1.span.extract()
            title_div = full_div.h1.div
            title_div.replaceWith(title_div.string)
            
            # clear the presentation area
            for div in full_div.findAll('div'):
                div.extract();
            
            # add qa list back to presentation area
            for qa_div in qa_div_list:
                full_div.insert(len(full_div.contents), qa_div)
        else:
            text_info = find_by_class(soup, 'div', 'text_info').next()
            for other in text_info.findAll('div'):
                other.extract()

        return soup