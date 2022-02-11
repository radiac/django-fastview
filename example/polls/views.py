import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from fastview import permissions
from fastview.viewgroups import ModelViewGroup
from fastview.views import generic
from fastview.views.filters import BooleanFilter

from .models import Choice, Question


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {"question": question, "error_message": "You didn't select a choice."},
        )
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


class RecentlyPublishedFilter(BooleanFilter):
    def process(self, qs):
        if self.boolean is None:
            return qs

        now = timezone.now()
        # The tutorial hard-codes the field name for simplicity
        # By using self.field_name this becomes more of a reusable filter
        date_range = {
            f"{self.field_name}__gte": now - datetime.timedelta(days=30),
            f"{self.field_name}__lte": now,
        }

        if self.boolean is True:
            return qs.filter(**date_range)
        return qs.exclude(**date_range)


class PollViewGroup(ModelViewGroup):
    model = Question
    permission = permissions.Public()

    index_view = generic.ListView.config(
        template_name="index.html",
        paginate_by=3,
    )
    list_view = generic.ListView.config(
        fields=["question_text", "pub_date", "was_published_recently"],
        filters=[
            "pub_date",
            RecentlyPublishedFilter(
                param="recently_published",
                field_name="pub_date",
                label="Recently published?",
            ),
        ],
        paginate_by=25,
    )
