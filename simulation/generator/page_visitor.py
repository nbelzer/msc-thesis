from .utils import Page
from .confined_list import ConfinedList


class PageVisitor:
    current_page: Page
    page_history: ConfinedList

    def __init__(self):
        self.page_history = ConfinedList()

    def next_pages(self):
        """Return the next page that can be visited through an outgoing link, or
        by going back in the page history.  Excludes the current_page.
        """
        outgoing_links = [ url for url in self.current_page.outgoing_links
                           if url != self.current_page.url ]
        if len(self.page_history) > 0:
            return outgoing_links + [ self.page_history.latest_item().url ]
        return outgoing_links

    def set_current_page(self, page: Page):
        self.page_history.push(page)
        self.current_page = page
