def polish_answer(answer:str):

    answer=answer.strip()

    # Make first sentence strong
    if answer.startswith("Yes, Shree Enterprise provides"):

        answer=answer.replace(
            "Yes, Shree Enterprise provides",
            "Yes, Shree Enterprise offers"
        )


    # Make business ending
    if "contact" not in answer.lower():

        answer+=" For complete details, you can contact Shree Enterprise."
    if "solar" in answer.lower():

        answer+="\n\nAvailable systems:\n• 2.5kW\n• 3kW\n• 5kW"

    # shorten overly long answers
    if len(answer)>450:

        answer=answer[:450]+"..."


    return answer