import re, urlparse, itertools
from calibre.ebooks.BeautifulSoup import NavigableString, Tag
from datetime import date, timedelta

language = 'en'

site_url = 'http://www.infoq.com/'

title_prefix = 'InfoQ'

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

'''
language = 'zh'

site_url = 'http://www.infoq.com/cn/'

title_prefix = 'InfoQ中国站'

date_regexes = [
    r'一月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'二月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'三月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'四月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'五月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'六月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'七月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'八月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'九月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'十月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'十一月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})',
    r'十二月\s+(?P<day>\d{2}),\s+(?P<year>\d{4})'
]
'''

# the sections to download
sections = [ 'news', 'articles', 'interviews' ]

# the range of date (both inclusive) to download
date_range = (date(2013, 6, 20), date(2013, 6, 22))

# the range of date to override for sections
section_date_ranges = {
    # 'news': (date(2013, 6, 21), date(2013, 6, 22)),
    # 'articles': (date(2013, 6, 5), date(2013, 6, 10)),
    # 'interviews': (date(2013, 1, 1), date(2013, 3, 1))
}

# do NOT touch the code below unless you know what to do

def range2str(range, shorten):
    year_fmt = '%Y%m%d'
    month_fmt = '%m%d'
    day_fmt = '%d'

    begin, end = range
    if begin == end:
        return begin.strftime(year_fmt)
    else:
        text = begin.strftime(year_fmt) + "~"
        if not shorten:
            return text + end.strftime(year_fmt)
        
        if begin.year == end.year and begin.month == end.month:
            return text + end.strftime(day_fmt)

        if begin.year == end.year:
            return text + end.strftime(month_fmt)
            
        return text + end.strftime(year_fmt)

def generate_title(prefix):
    text = prefix + ' ' + range2str(date_range, True)
    
    for sec in sections:
        range = section_date_ranges.get(sec)
        if range:
            text = text + ' ' + sec[0].upper() + range2str(range, True)
    
    return text

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

_section_texts = {}
_section_item_classes = {
    'news': ['news_type_block'],
    'articles': ['news_type1', 'news_type2'],
    'interviews': ['news_type_video']
}
        
class InfoQ(BasicNewsRecipe):
    title = title_prefix
    
    language = language
    
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
            print '>>> Loading items from ' + section + '/' + str(count)

            root = self.index_to_soup(site_url + section + '/' + str(count))
            content_div = root.find('div', { 'id': 'content' })
            
            if not text_retrieved:
                text_retrieved = True
                text = content_div.h2.string.strip()
                _section_texts[section] = text
                print '>>> Text for section "' + section + '": ' + text
                
            for item_class in _section_item_classes[section]:
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
        self.title = generate_title(self.title)
    
        index = []
        
        for sec in sections:
            item_list = []
        
            range = section_date_ranges.get(sec)
            if not range: range = date_range
            
            begin, end = range
            for item in self.get_items(sec):
                date = item['date']
                
                if date > end: continue
                if date < begin: break

                item_list.append(item)
            
            index.append((_section_texts[sec] + ' (' + range2str(range, False) + ')', item_list))

        return index
    
    def postprocess_html(self, soup, first_fetch):
        author_general = soup.find('span', { 'class': 'author_general' })
        author_general.em.extract()
    
        # the complete content
        full_div = None
    
        transcript_div = soup.find('div', { 'id': 'transcript' })
        if transcript_div: # that's an interview
            # get all <div class="qa" />
            qa_div_list = list(find_by_class(transcript_div, 'div', 'qa'))
            for qa_div in qa_div_list:
                qa_div.extract()
                
                # replace all <a class="question_link">...</a> with <strong>...</strong>
                question_link = qa_div.find('a', { 'class': 'question_link' })
                question_strong = Tag(soup, 'strong')
                question_strong.append(question_link.string)
                question_link.replaceWith(question_strong)
            
            full_div = find_by_class(soup.find('div', { 'id': 'content' }), 'div', 'presentation_full').next()
            
            # clean the <h1 />
            full_div.h1.span.extract()
            title_div = full_div.h1.div
            title_div.replaceWith(title_div.string)
            
            # clear the presentation area
            for div in full_div.findAll('div'):
                div.extract()
            
            # add qa list back to presentation area
            for qa_div in qa_div_list:
                full_div.append(qa_div)
        else:
            # text only without title
            text_div = find_by_class(soup, 'div', 'text_info').next()
            text_div.extract()
            
            for other in text_div.findAll('div'):
                other.extract()
            
            # full_div contains title
            full_div = soup.find('div', { 'id': 'content' })
            for other in full_div.findAll('div'):
                other.extract()
            
            full_div.append(text_div)

        # keep full_div in <body /> only
        full_div.extract()
        
        for other in soup.body:
            other.extract()
            
        soup.body.append(full_div)

        return soup