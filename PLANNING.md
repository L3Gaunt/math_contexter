High-level plan, where it's going for MINIMAL functionality
- a entity highlighter/definition + reference extractor that works on plain text
- a simple scroll function where you can enter a range, and it prints the text + the referenced definitions

More detailed plan for research. Concrete things:
 [PROGRESS] set up an environment to try different prompts/workflows?
      [PROGRESS] upload on langfuse??
          [PROGRESS] Upload the entire chunk-splitted dataset to langfuse in a way that I can run experiments on the thing with different prompts.
 [ ] figure out how to extract INTRODUCTIONS of concepts
     - [PROGRESS] try the simplest possible thing, wrapping in @@@$$$.
     - [ ] if not good enough: compare with other approaches like first extracting entities
 [ ] figure out how to extract REFERENCES to concepts


What is the 

simplest case: Just extract, 2 calls for concepts and 
- Make a shitty entity extractor in text
- Make it work better in 

- make the extraction of entities work. Strategies
  - extract entities
  - think of the 
- first: making it bad is actually an OK product!!
- make a viewer that prints references on the side
  - (1 day if I am good, 3 if I am not)


- make the thing work with system prompt
- make it work with 

- manually annotate one input and target output?

- 


- experiment with system prompts in langsmith? -> visually inspect how well it does


- split text into chunks of varying lengths automatically -> NOT NOW
- manually, 5 chunks -> YES


21.3.
Where do I want to be in 3 hours? (11:33)
- have annotated
- 
- get something to work with langfuse/different endpoints?

- getting Langfuse to work: NOT, because I will try different prompts/approaches anyway?? Or, only for those I can do quickly/manually inspect

Where do I want to be in 30 minutes?


More interesting talk: 

Have 


12:34 actually, extracting the segments where stuff is being defined seems like it should be the first step!
12:42 Plan: first try extraction of definitions in multiple steps, then do extraction again

13:01 was at the talk.
13:08 okay, next step: try concept extraction

idea: separate extraction of definitions/theorems from extraction of variable names, because the latter need much smaller chunks

okay, plan next 2 hrs:


14:51 what did I do in the last three hours?
  - had the insight that I should first do definition/theorem extraction
  - signed up in langfuse

15:15 next check-in: 15:45?
till then:
  - get some longer extracts
check in 15:52:
  - made more detailed checklist, next checkin: 16:30
  - next 60 secs: looked over things to see if they are applicable <- DONE

next: try extraction system prompt on different models + lengths + extraction approaches

- log on on langchain
- try approaches:


check in 16:30, till then: want to have a concrete plan


16:52 late 16:30 check in. I did log on on langfuse, and tried to get the prompt work on the dataset. It didn't work. Next: See tutorial. Next checkin: 17:20

17:35 found that the problem is in the fact that the csv input was not in json format, tried to debug how to connect langfuse mcp server <- stop that, instead do API in .env

next checkin: 18:00
18:16 late checkin: got stuff to upload to langtrace!

next checkin: 18:30 till then: try some prompts

18:30 checkin: I didn't yet see things in langfuse. next checkin: 19:00. till then: get

19:00 didn't understand, didn't finish the thought before. Next checkin: 20:30. till then: make a prompt to upload nothing to langfuse except the chunked dataset, in a way that I don't hit rate limits and can experiment to it in the API.

finished that planning at 19:13



very next thing: make a better prompt for the langfuse integration that does nothing but
 - upload the dataset
 - add tracing to evaluation.
 - get to the point that 