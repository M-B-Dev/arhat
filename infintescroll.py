IMAGES_URLS = ['https://upload.wikimedia.org/wikipedia/commons/c/c3/Jordan_by_Lipofsky_16577.jpg' for _ in range(5)]




class InfinityScrollView(ScrollView):
    def on_scroll_move(self, touch):
        if self.scroll_y < 0:
            self.upload_images(self)
        return super(InfinityScrollView, self).on_scroll_move(touch)

    def upload_images(self):
        layout = self.children[0]
        layout_childrens = len(layout.children)
        for url in IMAGES_URLS:
            img = AsyncImage(source=url, size_hint_y=None, height=240)
            layout.add_widget(img)
        bar_position = layout_childrens / (layout_childrens + len(IMAGES_URLS))
        self.scroll_y = 100 - 100 * bar_position
        self.effect_y.value = self.effect_y.min - self.effect_y.min * bar_position


class InfiniteScrollApp(App):
    def build(self):
        layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        for url in IMAGES_URLS:
            img = AsyncImage(source=url, size_hint_y=None,
                             height=240)
            layout.add_widget(img)
        root = InfinityScrollView(size_hint=(None, None), size=(400, 400),
                                  pos_hint={'center_x': .5, 'center_y': .5})
        root.add_widget(layout)
        return root
