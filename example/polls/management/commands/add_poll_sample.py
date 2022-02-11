import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from polls.models import Choice, Question


class Command(BaseCommand):
    help = "Add sample poll data"

    def handle(self, *args, **options):

        start = timezone.now() - datetime.timedelta(weeks=75)
        for i in range(150):
            question = Question.objects.create(
                question_text=f"Question {i+1}",
                pub_date=start + datetime.timedelta(weeks=i),
            )
            Choice.objects.bulk_create(
                [
                    Choice(question=question, choice_text=f"Answer {j+1}")
                    for j in range(5)
                ]
            )

        self.stdout.write(self.style.SUCCESS("Created 150 questions"))
