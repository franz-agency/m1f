# Scraped from http://localhost:8080/page/complex-layout

*Scraped at: 2025-05-23 11:21:49*

*Source URL: http://localhost:8080/page/complex-layout*

---


## Flexbox Layouts

Testing various flexbox configurations and how they convert to Markdown.

### Flex Item 1

This is a flexible item that can grow and shrink based on available space.

- Feature 1
- Feature 2
- Feature 3

### Flex Item 2

Another flex item with different content length to test alignment.

```
const flexbox = {
  display: 'flex',
  gap: '2rem'
};
```

### Flex Item 3

Short content.




## CSS Grid Layouts

Complex grid layouts with spanning items and auto-placement.

### Large Grid Item

This item spans 2 columns and 2 rows in the grid layout.

Grid areas can contain complex content including nested elements.


#### Grid Item 2

Regular sized item.


#### Grid Item 3

`grid-template-columns`

#### Grid Item 4

Auto-placed in the grid.


#### Grid Item 5

Another auto-placed item.




## Deeply Nested Structures

Testing how deeply nested HTML elements are converted to Markdown.

### Level 1 - Outer Container

This is the outermost level of nesting.

#### Level 2 - First Nested

Content at the second level of nesting.

- Item 1
  - Subitem 1.1
  - Subitem 1.2
- Item 2

##### Level 3 - Deeply Nested

Content at the third level of nesting.

> A blockquote within nested content.
> 
> > A nested blockquote for extra complexity.

###### Level 4 - Maximum Nesting

This is getting quite deep!

```
// Code within deeply nested structure
function deeplyNested() {
    return {
        level: 4,
        message: "Still readable!"
    };
}
```



#### Level 2 - Second Nested

Another branch at the second level.

| Nested | Table |
| --- | --- |
| Cell 1 | Cell 2 |




## Complex Positioning

Absolute Top Left


Absolute Top Right


Absolute Bottom Center


### Relative Content

This content is within a relatively positioned container with absolutely positioned elements.




## Multi-Column Layout

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium, totam rem aperiam, eaque ipsa quae ab illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo.

Nemo enim ipsam voluptatem quia voluptas sit aspernatur aut odit aut fugit, sed quia consequuntur magni dolores eos qui ratione voluptatem sequi nesciunt.



## Text Wrapping with Shapes

This text wraps around a circular shape using CSS shape-outside property. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.

After the float is cleared, text returns to normal flow.


## Masonry Layout

### Card 1

Short content


### Card 2

Medium length content that takes up more vertical space in the masonry layout.

- Point 1
- Point 2

### Card 3

Very long content that demonstrates how masonry layout handles different content heights. This card has multiple paragraphs.

Second paragraph with more details about the masonry layout behavior.

Third paragraph to make this card even taller.


### Card 4

`masonry-auto-flow`

### Card 5

Another card with medium content.

> A quote within a masonry item.




## Overflow Containers

Testing scrollable containers with overflow content.

### Scrollable Content Area

This container has a fixed height and scrollable overflow.

1. First item in scrollable list
2. Second item in scrollable list
3. Third item in scrollable list
4. Fourth item in scrollable list
5. Fifth item in scrollable list
6. Sixth item in scrollable list
7. Seventh item in scrollable list
8. Eighth item in scrollable list
9. Ninth item in scrollable list
10. Tenth item in scrollable list

More content after the list to ensure scrolling is needed.






