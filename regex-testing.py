import re
regex_insert_space = re.compile('\.(If|Else|Otherwise|For|Set|No|This|Or|Email)', re.IGNORECASE)
regex_hyphen_sentence = re.compile('-\s+(If\s|When\s)', re.IGNORECASE)

text = u'For Email, After the existing alliance validation is complete,\
there is a third party service call for further validation.Email address should not be in \
Relevates suppression list, mail box of the domain should not be blocked and it \
should not be in the domain where, the email is not accepted.If this is OK.Else ignore - If another, then new line.'
#print(text)
text = 'between oct and March of this year'
between_month_year = re.compile('between\s*(jan(?:uary)?|feb(?:uary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?\
|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*(and|&)\s*(jan(?:uary)?|feb(?:uary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?\
|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s*.*\s*(\d{4}|this year|last year)', re.I)
match = between_month_year.match(text)
print(match.groups())
#date_entities = [('january','feb')]
print('count of matches:', len(match.groups()))
text = regex_insert_space.sub(r'. \1',text)
text = regex_hyphen_sentence.sub(r'. \1', text)
print('-----')
print(text)